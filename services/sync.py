"""
Фоновые воркеры синхронизации с 1С.
Обновлено под новую модель: Product + ProductVariant + Brand.
"""
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from config import settings
from db import get_session
from models import (
    Product, ProductVariant, Category, Brand,
    Order, SyncLog, OrderEvent,
)
from services.onec_client import Client1C, OneCError

logger = logging.getLogger(__name__)


def make_client() -> Client1C:
    return Client1C(
        base_url=settings.ONE_C_URL,
        username=settings.ONE_C_USER,
        password=settings.ONE_C_PASSWORD,
        timeout=settings.ONE_C_TIMEOUT,
    )


# ─── Главные циклы ────────────────────────────────────────────────────────────

async def products_loop():
    client = make_client()
    while True:
        await _run("products", lambda: sync_catalog(client))
        await asyncio.sleep(settings.SYNC_PRODUCTS_INTERVAL)


async def stock_loop():
    client = make_client()
    while True:
        await _run("stock", lambda: sync_stock(client))
        await asyncio.sleep(settings.SYNC_STOCK_INTERVAL)


async def orders_loop():
    client = make_client()
    while True:
        await _run("orders", lambda: sync_order_statuses(client))
        await asyncio.sleep(settings.SYNC_ORDERS_INTERVAL)


async def payments_loop():
    client = make_client()
    while True:
        await _run("payments", lambda: sync_payments(client))
        await asyncio.sleep(settings.SYNC_PAYMENTS_INTERVAL)


async def _run(name: str, fn):
    started = datetime.now(timezone.utc)
    try:
        stats = await fn()
        await _write_log(name, "ok", started, **stats)
        logger.info("[sync %s] %s", name, stats)
    except OneCError as exc:
        await _write_log(name, "error", started, error=str(exc))
        logger.error("[sync %s] error: %s", name, exc)
    except Exception as exc:
        await _write_log(name, "error", started, error=str(exc))
        logger.exception("[sync %s] unexpected error", name)


# ─── Каталог: бренды, категории, товары, варианты ────────────────────────────

async def sync_catalog(client: Client1C) -> dict:
    """Полная синхронизация каталога из 1С."""
    brands_raw     = await client.get_brands()
    categories_raw = await client.get_categories()
    products_raw   = await client.get_products()
    variants_raw   = await client.get_variants()

    async with get_session() as db:
        brand_map    = await _sync_brands(db, brands_raw)
        category_map = await _sync_categories(db, categories_raw)
        product_map  = await _sync_products(db, products_raw, brand_map, category_map)
        v_stats      = await _sync_variants(db, variants_raw, product_map)
        await db.commit()

    return {
        "brands":     len(brand_map),
        "categories": len(category_map),
        "products":   len(product_map),
        **v_stats,
    }


async def _sync_brands(db, brands_raw):
    result = await db.execute(select(Brand))
    existing = {b.code: b for b in result.scalars().all()}
    out = {}
    for b in brands_raw:
        code = b["code"]
        if code in existing:
            brand = existing[code]
            brand.name = b["name"]
            brand.sort_order = b.get("sort", 0)
        else:
            brand = Brand(code=code, name=b["name"], sort_order=b.get("sort", 0))
            db.add(brand)
            await db.flush()
        out[code] = brand.id
    return out


async def _sync_categories(db, categories_raw):
    """Двухпроходно: сначала родители, потом дети — чтобы parent_id связались."""
    result = await db.execute(select(Category))
    existing = {c.one_c_id: c for c in result.scalars().all()}
    out = {}

    # Первый проход — все категории без parent_id
    for c in categories_raw:
        one_c_id = c["id"]
        if one_c_id in existing:
            cat = existing[one_c_id]
            cat.name = c["name"]
            cat.sort_order = c.get("sort", 0)
        else:
            cat = Category(
                one_c_id=one_c_id, name=c["name"],
                sort_order=c.get("sort", 0),
            )
            db.add(cat)
            await db.flush()
            existing[one_c_id] = cat
        out[one_c_id] = cat.id

    # Второй проход — связываем parent
    for c in categories_raw:
        if c.get("parent"):
            existing[c["id"]].parent_id = out.get(c["parent"])

    return out


async def _sync_products(db, products_raw, brand_map, category_map):
    result = await db.execute(select(Product))
    existing = {p.one_c_id: p for p in result.scalars().all()}
    out = {}

    seen = set()
    for p in products_raw:
        one_c_id = p["one_c_id"]
        seen.add(one_c_id)
        brand_id    = brand_map.get(p.get("brand_code"))
        category_id = category_map.get(p.get("category_one_c_id"))

        if one_c_id in existing:
            prod = existing[one_c_id]
            prod.name       = p["name"]
            prod.short_name = p.get("short_name", "")
            prod.brand_id   = brand_id
            prod.category_id = category_id
            prod.is_active  = p.get("is_active", True)
            prod.image_url  = p.get("image_url", "")
        else:
            prod = Product(
                one_c_id=one_c_id, name=p["name"],
                short_name=p.get("short_name", ""),
                brand_id=brand_id, category_id=category_id,
                is_active=p.get("is_active", True),
                image_url=p.get("image_url", ""),
            )
            db.add(prod)
            await db.flush()
        out[one_c_id] = prod.id
        prod.updated_at = datetime.now(timezone.utc)

    # Деактивируем удалённые товары
    for one_c_id, prod in existing.items():
        if one_c_id not in seen and prod.is_active:
            prod.is_active = False

    return out


async def _sync_variants(db, variants_raw, product_map):
    result = await db.execute(select(ProductVariant))
    existing = {v.one_c_id: v for v in result.scalars().all()}
    created = updated = 0

    for v in variants_raw:
        one_c_id   = v["one_c_id"]
        product_id = product_map.get(v.get("product_one_c_id"))
        if not product_id:
            continue

        price = v.get("price")
        price_dec = Decimal(str(price)) if price is not None else None

        if one_c_id in existing:
            var = existing[one_c_id]
            var.product_id   = product_id
            var.sku          = v["sku"]
            var.pack_size    = v["pack_size"]
            var.price        = price_dec
            var.is_orderable = v.get("is_orderable", True)
            var.stock_qty    = v.get("stock_qty", 0)
            var.unit         = v.get("unit", "упак")
            var.sort_order   = v.get("sort_order", 0)
            updated += 1
        else:
            var = ProductVariant(
                one_c_id=one_c_id, product_id=product_id,
                sku=v["sku"], pack_size=v["pack_size"],
                price=price_dec,
                is_orderable=v.get("is_orderable", True),
                stock_qty=v.get("stock_qty", 0),
                unit=v.get("unit", "упак"),
                sort_order=v.get("sort_order", 0),
            )
            db.add(var)
            created += 1

    return {"variants_created": created, "variants_updated": updated}


# ─── Остатки ──────────────────────────────────────────────────────────────────

async def sync_stock(client: Client1C) -> dict:
    """Обновляет stock_qty у ProductVariant по SKU."""
    raw = await client.get_stock()
    updated = 0

    async with get_session() as db:
        for item in raw:
            result = await db.execute(
                select(ProductVariant).where(ProductVariant.sku == item["sku"])
            )
            var = result.scalar_one_or_none()
            if var and var.stock_qty != item["qty"]:
                var.stock_qty = item["qty"]
                var.stock_updated_at = datetime.now(timezone.utc)
                updated += 1
        await db.commit()

    return {"updated": updated}


# ─── Статусы заказов ─────────────────────────────────────────────────────────

async def sync_order_statuses(client: Client1C) -> dict:
    active = ("invoiced", "paid", "shipped")
    updated = 0

    async with get_session() as db:
        result = await db.execute(
            select(Order).where(Order.status.in_(active), Order.one_c_id.is_not(None))
        )
        orders = result.scalars().all()
        if not orders:
            return {"updated": 0}

        ids = [o.one_c_id for o in orders]
        statuses = await client.get_order_statuses(ids)

        STATUS_MAP = {
            "Отгружен":  "shipped",
            "Доставлен": "delivered",
            "Отменён":   "cancelled",
        }
        for order in orders:
            new_status = STATUS_MAP.get(statuses.get(order.one_c_id))
            if new_status and order.status != new_status:
                order.status = new_status
                order.updated_at = datetime.now(timezone.utc)
                db.add(OrderEvent(
                    order_id=order.id,
                    event_type="status_changed",
                    payload={"new_status": new_status},
                ))
                updated += 1

        await db.commit()
    return {"updated": updated}


# ─── Платежи ──────────────────────────────────────────────────────────────────

async def sync_payments(client: Client1C) -> dict:
    paid = 0
    async with get_session() as db:
        result = await db.execute(
            select(Order).where(Order.status == "invoiced", Order.one_c_id.is_not(None))
        )
        orders = result.scalars().all()

        for order in orders:
            try:
                info = await client.get_payment_status(order.one_c_id)
            except OneCError:
                continue
            if info.get("paid"):
                order.status = "paid"
                if info.get("paid_at"):
                    order.paid_at = datetime.fromisoformat(info["paid_at"])
                order.updated_at = datetime.now(timezone.utc)
                db.add(OrderEvent(
                    order_id=order.id,
                    event_type="payment_received",
                    payload={"amount": info.get("amount")},
                ))
                paid += 1

        await db.commit()
    return {"paid": paid}


# ─── Лог ──────────────────────────────────────────────────────────────────────

async def _write_log(entity: str, status: str, started_at: datetime, **details: Any):
    finished = datetime.now(timezone.utc)
    duration = int((finished - started_at).total_seconds() * 1000)
    async with get_session() as db:
        db.add(SyncLog(
            entity=entity, status=status,
            started_at=started_at, finished_at=finished,
            duration_ms=duration, details=details,
        ))
        await db.commit()

"""
Mock 1С — заглушка с реальным каталогом Albatros Healthcare.

Запуск:
  uvicorn mock_1c.server:app --host 0.0.0.0 --port 8001 --reload
"""
import random
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query

from mock_1c.catalog_data import BRANDS, CATEGORIES, PRODUCTS

app = FastAPI(title="Mock 1С Server — Albatros")


# ─── Тестовые клиенты (контрагенты в 1С) ─────────────────────────────────────

CLIENTS = {
    "300123456": {
        "one_c_id": "11111111-1111-1111-1111-111111111111",
        "name":     "Городская клиническая больница №1",
        "tier":     "vip",
        "type":     "government",
        "phone":    "+998 71 123-45-67",
        "address":  "Ташкент, ул. Хакимова 45",
    },
    "200987654": {
        "one_c_id": "22222222-2222-2222-2222-222222222222",
        "name":     "Медцентр «Здоровье+»",
        "tier":     "standard",
        "type":     "clinic",
        "phone":    "+998 90 555-12-34",
        "address":  "Ташкент, Юнусабадский р-н, 12",
    },
    "300555111": {
        "one_c_id": "33333333-3333-3333-3333-333333333333",
        "name":     "Частная стоматология «Дент»",
        "tier":     "limited",
        "type":     "clinic",
        "phone":    "+998 71 999-99-99",
        "address":  "Ташкент, ул. Амира Темура 1",
    },
}


# ─── Подготовка каталога: разворачиваем PRODUCTS в плоский список ───────────

def _build_catalog():
    """Генерирует SKU и one_c_id, возвращает плоский список товаров и вариантов."""
    brands = {b["code"]: b for b in BRANDS}
    products_out = []
    variants_out = []

    for idx, (name, short, cat_id, brand_code, variants) in enumerate(PRODUCTS):
        product_one_c_id = f"prod-{idx:04d}"
        for v_idx, v in enumerate(variants):
            sku = f"{short.replace(' ', '_').replace('/', '_')}-{v['pack'].split()[0].replace('×', 'x')[:10]}"
            sku = sku.replace("/", "_").replace(",", "").replace(".", "").upper()
            sku = f"{sku}-{idx:04d}{v_idx}"
            variants_out.append({
                "one_c_id":     f"var-{idx:04d}-{v_idx}",
                "product_one_c_id": product_one_c_id,
                "sku":          sku,
                "pack_size":    v["pack"],
                "price":        v["price"],
                "is_orderable": v["price"] is not None,
                "stock_qty":    random.randint(20, 500) if v["price"] else 0,
                "unit":         "упак",
                "sort_order":   v_idx,
            })
        products_out.append({
            "one_c_id":    product_one_c_id,
            "name":        name,
            "short_name":  short,
            "category_one_c_id": cat_id,
            "brand_code":  brand_code,
            "is_active":   True,
            "image_url":   "",
        })

    return brands, CATEGORIES, products_out, variants_out


BRANDS_DICT, CATEGORIES_LIST, PRODUCTS_LIST, VARIANTS_LIST = _build_catalog()

# In-memory хранилище заказов
ORDERS: dict[str, dict] = {}


# ─── Эндпоинты 1С ────────────────────────────────────────────────────────────

@app.get("/hs/clients/check")
async def check_client(inn: str = Query(...)):
    if inn not in CLIENTS:
        return {"found": False}
    return {"found": True, "inn": inn, **CLIENTS[inn]}


@app.get("/hs/catalog/brands")
async def get_brands():
    return BRANDS


@app.get("/hs/catalog/categories")
async def get_categories():
    return CATEGORIES_LIST


@app.get("/hs/catalog/products")
async def get_products():
    return PRODUCTS_LIST


@app.get("/hs/catalog/variants")
async def get_variants():
    return VARIANTS_LIST


@app.get("/hs/catalog/stock")
async def get_stock():
    return [{"sku": v["sku"], "qty": v["stock_qty"]} for v in VARIANTS_LIST if v["is_orderable"]]


@app.post("/hs/orders/create-with-invoice")
async def create_order(payload: dict):
    one_c_id = str(uuid.uuid4())
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{len(ORDERS) + 1:04d}"
    total = sum(item["subtotal"] for item in payload.get("items", []))

    ORDERS[one_c_id] = {
        "one_c_id":       one_c_id,
        "external_ref":   payload.get("external_ref"),
        "items":          payload.get("items", []),
        "total":          total,
        "invoice_number": invoice_number,
        "status":         "Создан",
        "paid":           False,
        "created_at":     datetime.now(timezone.utc).isoformat(),
    }

    return {
        "one_c_id":       one_c_id,
        "invoice_number": invoice_number,
        "invoice_url":    "https://www.africau.edu/images/default/sample.pdf",
        "contract_url":   "https://www.africau.edu/images/default/sample.pdf",
        "total_amount":   total,
    }


@app.get("/hs/orders/{order_id}/payment-status")
async def payment_status(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(404, "Order not found")
    order = ORDERS[order_id]
    return {
        "paid":    order["paid"],
        "amount":  order["total"] if order["paid"] else 0,
        "paid_at": datetime.now(timezone.utc).isoformat() if order["paid"] else None,
    }


@app.post("/hs/orders/statuses")
async def get_statuses(payload: dict):
    ids = payload.get("ids", [])
    return {oid: ORDERS[oid]["status"] for oid in ids if oid in ORDERS}


# ─── Админ-эндпоинты (для тестирования) ──────────────────────────────────────

@app.post("/_admin/orders/{order_id}/mark-paid")
async def mark_paid(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(404, "Order not found")
    ORDERS[order_id]["paid"] = True
    ORDERS[order_id]["status"] = "Оплачен"
    return {"ok": True, "order_id": order_id}


@app.post("/_admin/orders/{order_id}/ship")
async def mark_shipped(order_id: str):
    if order_id not in ORDERS:
        raise HTTPException(404, "Order not found")
    ORDERS[order_id]["status"] = "Отгружен"
    return {"ok": True, "order_id": order_id}


@app.get("/_admin/orders")
async def list_orders():
    return list(ORDERS.values())


@app.get("/")
async def root():
    return {
        "name": "Mock 1С Albatros",
        "catalog": {
            "brands":   len(BRANDS),
            "categories": len(CATEGORIES_LIST),
            "products": len(PRODUCTS_LIST),
            "variants": len(VARIANTS_LIST),
        },
        "test_inns": list(CLIENTS.keys()),
    }

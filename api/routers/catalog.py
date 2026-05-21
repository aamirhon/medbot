"""
Эндпоинты каталога для Mini App.

Изменения по сравнению с MVP-версией:
  • ProductOut содержит список variants (id, sku, pack_size, price, is_orderable, stock_qty)
  • Фильтр по brand_id
  • Отдельный эндпоинт GET /catalog/brands
  • Фильтр по категории учитывает подкатегории (рекурсивно через Python, не CTE)
  • Фильтр по цене применяется к минимальной цене среди вариантов
"""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_

from db import get_session
from models import Category, Product, ProductVariant, Brand, User
from api.auth import get_current_user

router = APIRouter(prefix="/catalog", tags=["catalog"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class BrandOut(BaseModel):
    id: str
    code: str
    name: str
    sort_order: int


class CategoryOut(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    product_count: int


class VariantOut(BaseModel):
    id: str
    sku: str
    pack_size: str        # "50 опред." / "100 опред." / "1x714 мл"
    price: Optional[float]  # None = "По запросу"
    is_orderable: bool
    stock_qty: int
    unit: str


class ProductOut(BaseModel):
    id: str
    name: str
    short_name: str
    category_id: Optional[str]
    brand_id: Optional[str]
    brand_name: Optional[str]   # подтягиваем сразу, чтобы фронт не делал N+1
    image_url: str
    variants: list[VariantOut]
    min_price: Optional[float]  # для сортировки/отображения в списке
    is_orderable: bool          # True если хотя бы один вариант orderable


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    per_page: int


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _collect_child_ids(db, parent_id: str) -> list[str]:
    """
    Рекурсивно собирает id категорий-потомков (включая сам parent_id).
    Для двухуровневой иерархии этого достаточно; если появится третий уровень —
    заменить на WITH RECURSIVE CTE.
    """
    ids = [parent_id]
    result = await db.execute(
        select(Category.id).where(Category.parent_id == parent_id)
    )
    children = result.scalars().all()
    for child_id in children:
        ids.extend(await _collect_child_ids(db, child_id))
    return ids


def _make_product_out(
    product: Product,
    variants: list[ProductVariant],
    brand_name: Optional[str],
) -> ProductOut:
    variant_outs = [
        VariantOut(
            id=v.id,
            sku=v.sku,
            pack_size=v.pack_size,
            price=float(v.price) if v.price is not None else None,
            is_orderable=v.is_orderable,
            stock_qty=v.stock_qty,
            unit=v.unit,
        )
        for v in variants
    ]
    orderable_prices = [
        float(v.price) for v in variants
        if v.is_orderable and v.price is not None
    ]
    return ProductOut(
        id=product.id,
        name=product.name,
        short_name=product.short_name,
        category_id=product.category_id,
        brand_id=product.brand_id,
        brand_name=brand_name,
        image_url=product.image_url,
        variants=variant_outs,
        min_price=min(orderable_prices) if orderable_prices else None,
        is_orderable=len(orderable_prices) > 0,
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/brands", response_model=list[BrandOut])
async def list_brands(_: User = Depends(get_current_user)):
    """Все бренды, отсортированные по sort_order."""
    async with get_session() as db:
        result = await db.execute(
            select(Brand).order_by(Brand.sort_order, Brand.name)
        )
        brands = result.scalars().all()
        return [
            BrandOut(id=b.id, code=b.code, name=b.name, sort_order=b.sort_order)
            for b in brands
        ]


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(_: User = Depends(get_current_user)):
    """
    Все категории с количеством товаров.
    product_count для родительских категорий — сумма товаров всех дочерних.
    """
    async with get_session() as db:
        # 1. Все категории
        cats_result = await db.execute(
            select(Category).order_by(Category.sort_order, Category.name)
        )
        all_cats = cats_result.scalars().all()

        # 2. Прямой подсчёт товаров по каждой категории
        counts_result = await db.execute(
            select(Product.category_id, func.count(Product.id).label("cnt"))
            .where(Product.is_active == True)
            .where(Product.category_id.isnot(None))
            .group_by(Product.category_id)
        )
        direct_counts = {row.category_id: row.cnt for row in counts_result}

        # 3. Карта parent_id → [child_ids]
        children_map: dict[str, list[str]] = {}
        for cat in all_cats:
            if cat.parent_id:
                children_map.setdefault(cat.parent_id, []).append(cat.id)

        # 4. Рекурсивная сумма (работает для двух уровней и глубже)
        def total_count(cat_id: str) -> int:
            own = direct_counts.get(cat_id, 0)
            return own + sum(total_count(cid) for cid in children_map.get(cat_id, []))

        return [
            CategoryOut(
                id=cat.id,
                name=cat.name,
                parent_id=cat.parent_id,
                product_count=total_count(cat.id),
            )
            for cat in all_cats
        ]


@router.get("/products", response_model=ProductListOut)
async def list_products(
    _: User = Depends(get_current_user),
    category_id: Optional[str] = None,
    brand_id: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=100),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    Список товаров с фильтрами и вариантами.

    Фильтры:
      category_id   — включает подкатегории
      brand_id      — по бренду
      search        — по name и short_name (ILIKE)
      min_price     — мин. цена среди вариантов (фильтруется в Python)
      max_price     — макс. цена среди вариантов (фильтруется в Python)
      in_stock_only — хотя бы один вариант в наличии
    """
    async with get_session() as db:
        # ── 1. Категории с подкатегориями ─────────────────────────────────
        category_ids: Optional[list[str]] = None
        if category_id:
            category_ids = await _collect_child_ids(db, category_id)

        # ── 2. Базовый запрос Products ────────────────────────────────────
        stmt = select(Product).where(Product.is_active == True)

        if category_ids:
            stmt = stmt.where(Product.category_id.in_(category_ids))

        if brand_id:
            stmt = stmt.where(Product.brand_id == brand_id)

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(pattern),
                    Product.short_name.ilike(pattern),
                )
            )

        # ── 3. Подтягиваем варианты ───────────────────────────────────────
        # Делаем отдельным запросом, чтобы не дублировать строки Product
        all_products = (await db.execute(stmt.order_by(Product.name))).scalars().all()

        if not all_products:
            return ProductListOut(items=[], total=0, page=page, per_page=per_page)

        product_ids = [p.id for p in all_products]
        variants_result = await db.execute(
            select(ProductVariant)
            .where(ProductVariant.product_id.in_(product_ids))
            .order_by(ProductVariant.price)
        )
        all_variants = variants_result.scalars().all()

        # Группируем варианты по product_id
        variants_by_product: dict[str, list[ProductVariant]] = {}
        for v in all_variants:
            variants_by_product.setdefault(v.product_id, []).append(v)

        # ── 4. Подтягиваем бренды ─────────────────────────────────────────
        brand_ids = {p.brand_id for p in all_products if p.brand_id}
        brands_map: dict[str, str] = {}
        if brand_ids:
            brands_result = await db.execute(
                select(Brand.id, Brand.name).where(Brand.id.in_(brand_ids))
            )
            brands_map = {row.id: row.name for row in brands_result}

        # ── 5. Собираем ProductOut и применяем ценовые фильтры ────────────
        product_outs: list[ProductOut] = []
        for product in all_products:
            variants = variants_by_product.get(product.id, [])
            out = _make_product_out(
                product,
                variants,
                brands_map.get(product.brand_id) if product.brand_id else None,
            )

            # Ценовые фильтры по min_price вариантов
            if min_price is not None and (
                out.min_price is None or out.min_price < min_price
            ):
                continue
            if max_price is not None and (
                out.min_price is None or out.min_price > max_price
            ):
                continue

            # Фильтр по наличию
            if in_stock_only:
                has_stock = any(
                    v.is_orderable and v.stock_qty > 0
                    for v in variants
                )
                if not has_stock:
                    continue

            product_outs.append(out)

        # ── 6. Пагинация ──────────────────────────────────────────────────
        total = len(product_outs)
        start = (page - 1) * per_page
        page_items = product_outs[start : start + per_page]

        return ProductListOut(
            items=page_items,
            total=total,
            page=page,
            per_page=per_page,
        )


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, _: User = Depends(get_current_user)):
    """Детали одного товара со всеми вариантами."""
    async with get_session() as db:
        product = await db.get(Product, product_id)
        if not product or not product.is_active:
            raise HTTPException(404, "Product not found")

        variants_result = await db.execute(
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.price)
        )
        variants = variants_result.scalars().all()

        brand_name: Optional[str] = None
        if product.brand_id:
            brand = await db.get(Brand, product.brand_id)
            brand_name = brand.name if brand else None

        return _make_product_out(product, variants, brand_name)

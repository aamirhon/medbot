"""Эндпоинты каталога: категории, товары, поиск, фильтры."""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_

from db import get_session
from models import Category, Product, User
from api.auth import get_current_user

router = APIRouter(prefix="/catalog", tags=["catalog"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    product_count: int


class ProductOut(BaseModel):
    id: str
    sku: str
    name: str
    price: float
    unit: str
    stock_qty: int
    image_url: str
    category_id: Optional[str]
    in_stock: bool


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    per_page: int


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(_: User = Depends(get_current_user)):
    """Все категории с количеством товаров в каждой."""
    async with get_session() as db:
        result = await db.execute(
            select(
                Category.id, Category.name, Category.parent_id,
                func.count(Product.id).label("product_count"),
            )
            .outerjoin(Product, (Product.category_id == Category.id) & (Product.is_active == True))
            .group_by(Category.id)
            .order_by(Category.sort_order, Category.name)
        )
        return [
            CategoryOut(id=r.id, name=r.name, parent_id=r.parent_id, product_count=r.product_count)
            for r in result
        ]


@router.get("/products", response_model=ProductListOut)
async def list_products(
    _: User = Depends(get_current_user),
    category_id: Optional[str] = None,
    search: Optional[str] = Query(None, max_length=100),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    Список товаров с фильтрами.
    Поиск идёт по name и sku (ILIKE — без учёта регистра).
    """
    async with get_session() as db:
        stmt = select(Product).where(Product.is_active == True)

        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Product.name.ilike(pattern), Product.sku.ilike(pattern)))

        if min_price is not None:
            stmt = stmt.where(Product.price >= Decimal(str(min_price)))
        if max_price is not None:
            stmt = stmt.where(Product.price <= Decimal(str(max_price)))

        if in_stock_only:
            stmt = stmt.where(Product.stock_qty > 0)

        # Подсчёт общего количества для пагинации
        total = (await db.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()

        # Сама страница
        items = (await db.execute(
            stmt.order_by(Product.name)
                .offset((page - 1) * per_page)
                .limit(per_page)
        )).scalars().all()

        return ProductListOut(
            items=[
                ProductOut(
                    id=p.id, sku=p.sku, name=p.name,
                    price=float(p.price), unit=p.unit, stock_qty=p.stock_qty,
                    image_url=p.image_url, category_id=p.category_id,
                    in_stock=p.stock_qty > 0,
                )
                for p in items
            ],
            total=total, page=page, per_page=per_page,
        )


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, _: User = Depends(get_current_user)):
    """Детали одного товара."""
    async with get_session() as db:
        product = await db.get(Product, product_id)
        if not product or not product.is_active:
            from fastapi import HTTPException
            raise HTTPException(404, "Product not found")
        return ProductOut(
            id=product.id, sku=product.sku, name=product.name,
            price=float(product.price), unit=product.unit,
            stock_qty=product.stock_qty, image_url=product.image_url,
            category_id=product.category_id, in_stock=product.stock_qty > 0,
        )

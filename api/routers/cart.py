from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db import get_session
from models import CartItem, Organization, Product, ProductVariant, User
from services.limits import check_can_add_to_cart

router = APIRouter(prefix="/cart", tags=["cart"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CartItemOut(BaseModel):
    id: str
    variant_id: str
    product_id: str
    product_name: str
    short_name: str
    pack_size: str
    sku: str
    unit: str
    unit_price: float
    quantity: int
    subtotal: float
    image_url: str
    stock_qty: int
    in_stock: bool
    is_orderable: bool


class CartOut(BaseModel):
    items: list[CartItemOut]
    total_items: int
    total_amount: float
    has_unavailable: bool


class AddToCartIn(BaseModel):
    variant_id: str
    quantity: int = Field(default=1, ge=1, le=10000)


class UpdateCartIn(BaseModel):
    quantity: int = Field(ge=1, le=10000)


# ─── Helper ──────────────────────────────────────────────────────────────────

async def _build_cart(db: AsyncSession, user_id: str) -> CartOut:
    result = await db.execute(
        select(CartItem, ProductVariant, Product)
        .join(ProductVariant, CartItem.variant_id == ProductVariant.id)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(CartItem.user_id == user_id)
        .order_by(CartItem.added_at)
    )
    rows = result.all()

    items: list[CartItemOut] = []
    for cart_item, variant, product in rows:
        unit_price = float(variant.price) if variant.price is not None else 0.0
        subtotal = unit_price * cart_item.quantity
        in_stock = cart_item.quantity <= variant.stock_qty
        items.append(CartItemOut(
            id=cart_item.id,
            variant_id=variant.id,
            product_id=product.id,
            product_name=product.name,
            short_name=product.short_name,
            pack_size=variant.pack_size,
            sku=variant.sku,
            unit=variant.unit,
            unit_price=unit_price,
            quantity=cart_item.quantity,
            subtotal=subtotal,
            image_url=product.image_url,
            stock_qty=variant.stock_qty,
            in_stock=in_stock,
            is_orderable=variant.is_orderable,
        ))

    has_unavailable = any(not item.in_stock or not item.is_orderable for item in items)
    total_items = sum(item.quantity for item in items)
    total_amount = sum(item.subtotal for item in items)

    return CartOut(
        items=items,
        total_items=total_items,
        total_amount=total_amount,
        has_unavailable=has_unavailable,
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("", response_model=CartOut)
async def get_cart(user: User = Depends(get_current_user)):
    async with get_session() as db:
        return await _build_cart(db, user.id)


@router.post("/items", response_model=CartOut)
async def add_to_cart(payload: AddToCartIn, user: User = Depends(get_current_user)):
    async with get_session() as db:
        variant = await db.get(ProductVariant, payload.variant_id)
        if not variant:
            raise HTTPException(404, "Вариант товара не найден")
        if not variant.is_orderable:
            raise HTTPException(400, "Этот товар доступен только по запросу")

        result = await db.execute(
            select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.variant_id == payload.variant_id,
            )
        )
        existing = result.scalar_one_or_none()

        new_qty = (existing.quantity if existing else 0) + payload.quantity

        if new_qty > variant.stock_qty:
            raise HTTPException(
                400,
                f"Недостаточно на складе. Доступно: {variant.stock_qty} {variant.unit}",
            )

        if user.org_id:
            org = await db.get(Organization, user.org_id)
            product = await db.get(Product, variant.product_id)
            check = await check_can_add_to_cart(db, org, product, new_qty)
            if not check.ok:
                raise HTTPException(400, check.reason)

        if existing:
            existing.quantity = new_qty
        else:
            db.add(CartItem(user_id=user.id, variant_id=payload.variant_id, quantity=new_qty))

        await db.commit()
        return await _build_cart(db, user.id)


@router.patch("/items/{item_id}", response_model=CartOut)
async def update_cart_item(
    item_id: str,
    payload: UpdateCartIn,
    user: User = Depends(get_current_user),
):
    async with get_session() as db:
        cart_item = await db.get(CartItem, item_id)
        if not cart_item or cart_item.user_id != user.id:
            raise HTTPException(404, "Позиция корзины не найдена")

        variant = await db.get(ProductVariant, cart_item.variant_id)

        if payload.quantity > variant.stock_qty:
            raise HTTPException(
                400,
                f"Недостаточно на складе. Доступно: {variant.stock_qty} {variant.unit}",
            )

        if user.org_id:
            org = await db.get(Organization, user.org_id)
            product = await db.get(Product, variant.product_id)
            check = await check_can_add_to_cart(db, org, product, payload.quantity)
            if not check.ok:
                raise HTTPException(400, check.reason)

        cart_item.quantity = payload.quantity
        await db.commit()
        return await _build_cart(db, user.id)


@router.delete("/items/{item_id}", response_model=CartOut)
async def remove_cart_item(item_id: str, user: User = Depends(get_current_user)):
    async with get_session() as db:
        cart_item = await db.get(CartItem, item_id)
        if not cart_item or cart_item.user_id != user.id:
            raise HTTPException(404, "Позиция корзины не найдена")

        await db.delete(cart_item)
        await db.commit()
        return await _build_cart(db, user.id)


@router.delete("", response_model=CartOut)
async def clear_cart(user: User = Depends(get_current_user)):
    async with get_session() as db:
        await db.execute(delete(CartItem).where(CartItem.user_id == user.id))
        await db.commit()
        return await _build_cart(db, user.id)

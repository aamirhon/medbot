from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db import get_session
from models import Order, OrderItem, Organization, User
from services.orders import create_order_from_cart, OrderCreationError
from services.sync import make_client

router = APIRouter(prefix="/orders", tags=["orders"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class OrderItemOut(BaseModel):
    id: str
    variant_id: str
    product_name: str
    pack_size: str
    sku: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderOut(BaseModel):
    id: str
    status: str
    total_amount: float
    comment: str
    invoice_number: Optional[str]
    invoice_url: Optional[str]
    contract_url: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    items: list[OrderItemOut]


class OrderListItemOut(BaseModel):
    id: str
    status: str
    total_amount: float
    invoice_number: Optional[str]
    items_count: int
    created_at: datetime


class CreateOrderIn(BaseModel):
    comment: str = Field(default="", max_length=500)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _item_to_out(item: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        id=item.id,
        variant_id=item.variant_id,
        product_name=item.product_name,
        pack_size=item.pack_size,
        sku=item.sku,
        quantity=item.quantity,
        unit_price=float(item.unit_price),
        subtotal=float(item.subtotal),
    )


def _order_to_out(order: Order, items: list[OrderItem]) -> OrderOut:
    return OrderOut(
        id=order.id,
        status=order.status,
        total_amount=float(order.total_amount),
        comment=order.comment,
        invoice_number=order.invoice_number,
        invoice_url=order.invoice_url,
        contract_url=order.contract_url,
        created_at=order.created_at,
        paid_at=order.paid_at,
        items=[_item_to_out(i) for i in items],
    )


async def _load_order_with_items(db: AsyncSession, order_id: str) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("", response_model=OrderOut)
async def create_order(
    payload: CreateOrderIn,
    user: User = Depends(get_current_user),
):
    if not user.org_id:
        raise HTTPException(400, "Организация не привязана к аккаунту")

    onec = make_client()
    async with get_session() as db:
        org = await db.get(Organization, user.org_id)
        if not org:
            raise HTTPException(400, "Организация не найдена")

        try:
            order = await create_order_from_cart(db, onec, user, org, payload.comment)
        except OrderCreationError as exc:
            raise HTTPException(400, str(exc))

        order = await _load_order_with_items(db, order.id)
        return _order_to_out(order, order.items)


@router.get("", response_model=list[OrderListItemOut])
async def list_orders(user: User = Depends(get_current_user)):
    async with get_session() as db:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        if not orders:
            return []

        order_ids = [o.id for o in orders]
        counts_result = await db.execute(
            select(OrderItem.order_id, func.count(OrderItem.id).label("cnt"))
            .where(OrderItem.order_id.in_(order_ids))
            .group_by(OrderItem.order_id)
        )
        counts = {row.order_id: row.cnt for row in counts_result}

        return [
            OrderListItemOut(
                id=o.id,
                status=o.status,
                total_amount=float(o.total_amount),
                invoice_number=o.invoice_number,
                items_count=counts.get(o.id, 0),
                created_at=o.created_at,
            )
            for o in orders
        ]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, user: User = Depends(get_current_user)):
    async with get_session() as db:
        order = await _load_order_with_items(db, order_id)
        if not order or order.user_id != user.id:
            raise HTTPException(404, "Заказ не найден")
        return _order_to_out(order, order.items)

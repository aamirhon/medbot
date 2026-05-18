"""Панель сотрудника: просмотр всех заказов, смена статуса."""
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select, desc

from db import get_session
from models import Order, Organization
from utils import require_active_user, format_money, status_label

router = Router()


@router.message(F.text == "⚙️ Панель сотрудника")
async def staff_panel(msg: Message):
    user = await require_active_user(msg)
    if not user or user.role not in ("staff", "accountant", "admin"):
        await msg.answer("Доступно только сотрудникам.")
        return

    async with get_session() as db:
        result = await db.execute(
            select(Order, Organization)
            .join(Organization, Organization.id == Order.org_id)
            .where(Order.status.in_(["invoiced", "paid", "shipped"]))
            .order_by(desc(Order.created_at))
            .limit(30)
        )
        orders = result.all()

    if not orders:
        await msg.answer("Активных заказов нет.")
        return

    text = "<b>Активные заказы:</b>\n\n"
    for order, org in orders:
        text += (
            f"№ {order.invoice_number or order.id[:8]} · {org.name}\n"
            f"  {format_money(order.total_amount)} · {status_label(order.status)}\n\n"
        )
    await msg.answer(text)

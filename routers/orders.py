"""История заказов клиента."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile,
)
from sqlalchemy import select, desc

from db import get_session
from models import Order
from utils import require_active_user, format_money, status_label

router = Router()


@router.message(Command("orders"))
@router.message(F.text == "📋 Мои заказы")
async def list_orders(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return

    async with get_session() as db:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user.id)
            .order_by(desc(Order.created_at))
            .limit(20)
        )
        orders = result.scalars().all()

    if not orders:
        await msg.answer("У вас пока нет заказов.")
        return

    text = "<b>Ваши последние заказы:</b>\n\n"
    rows = []
    for o in orders:
        title = f"№ {o.invoice_number or o.id[:8]}"
        text += (
            f"• {title} — {format_money(o.total_amount)}\n"
            f"  {status_label(o.status)} · {o.created_at.strftime('%d.%m.%Y')}\n\n"
        )
        rows.append([InlineKeyboardButton(
            text=f"{title} · {status_label(o.status)}",
            callback_data=f"order:{o.id}",
        )])

    await msg.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("order:"))
async def show_order(cb: CallbackQuery):
    order_id = cb.data.split(":")[1]

    async with get_session() as db:
        order = await db.get(Order, order_id)
        if not order:
            await cb.answer("Заказ не найден", show_alert=True)
            return

        from models import OrderItem, Product
        result = await db.execute(
            select(OrderItem, Product)
            .join(Product, Product.id == OrderItem.product_id)
            .where(OrderItem.order_id == order_id)
        )
        items = result.all()

    text = (
        f"<b>Заказ № {order.invoice_number or order.id[:8]}</b>\n\n"
        f"Статус: {status_label(order.status)}\n"
        f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Состав заказа:</b>\n"
    )
    for item, product in items:
        text += f"• {product.name}\n  {item.quantity} × {format_money(item.unit_price)} = {format_money(item.subtotal)}\n"
    text += f"\n<b>Итого: {format_money(order.total_amount)}</b>"

    if order.comment:
        text += f"\n\nКомментарий: {order.comment}"

    await cb.message.answer(text)

    if order.status == "invoiced" and order.invoice_url:
        await cb.message.answer_document(
            URLInputFile(order.invoice_url, filename=f"invoice_{order.invoice_number}.pdf"),
            caption="📄 Счёт на оплату",
        )
    await cb.answer()

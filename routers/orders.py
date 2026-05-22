"""Read-only last-5 orders view."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import desc, select

from db import get_session
from i18n import t
from models import Order
from utils import require_active_user

router = Router()

_ORDERS_LABELS = frozenset({t("menu.orders", "ru"), t("menu.orders", "uz")})


@router.message(Command("orders"))
@router.message(F.text.in_(_ORDERS_LABELS))
async def list_orders(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return

    lang = user.language or "ru"

    async with get_session() as db:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user.id)
            .order_by(desc(Order.created_at))
            .limit(5)
        )
        orders = result.scalars().all()

    if not orders:
        await msg.answer(t("orders.empty", lang))
        return

    text = t("orders.header", lang)
    invoice_buttons: list[list[InlineKeyboardButton]] = []

    for o in orders:
        order_num = o.invoice_number or o.id[:8]
        date_str = o.created_at.strftime("%Y-%m-%d %H:%M")
        status = t(f"orders.statuses.{o.status}", lang)
        total = f"{float(o.total_amount):,.0f} сум".replace(",", " ")

        text += (
            f"\n<b>№ {order_num}</b>\n"
            f"📅 {date_str}  •  {status}\n"
            f"💰 {total}\n"
        )

        if o.invoice_url:
            invoice_buttons.append([InlineKeyboardButton(
                text=f"{t('orders.invoice_btn', lang)} — № {order_num}",
                url=o.invoice_url,
            )])

    kb = InlineKeyboardMarkup(inline_keyboard=invoice_buttons) if invoice_buttons else None
    await msg.answer(text, reply_markup=kb, disable_web_page_preview=True)

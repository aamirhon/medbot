"""
Корзина и оформление заказа.
При оформлении: создаём заказ → отправляем в 1С → получаем счёт + договор → шлём клиенту PDF.
"""
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile,
)
from sqlalchemy import select

from db import get_session
from models import CartItem, Product
from services.orders import create_order_from_cart, OrderCreationError
from services.sync import make_client
from utils import require_active_user, format_money, get_user_with_org

logger = logging.getLogger(__name__)
router = Router()


class CheckoutStates(StatesGroup):
    comment = State()


# ─── Просмотр корзины ────────────────────────────────────────────────────────

@router.message(Command("cart"))
@router.message(F.text == "🛒 Корзина")
async def show_cart(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return
    await _render_cart(msg, user.id)


async def _render_cart(msg: Message, user_id: str, edit: bool = False):
    async with get_session() as db:
        result = await db.execute(
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.user_id == user_id)
        )
        items = result.all()

    if not items:
        text = "Корзина пуста.\n\nОткройте каталог чтобы выбрать товары."
        await (msg.edit_text if edit else msg.answer)(text)
        return

    text = "<b>Ваша корзина</b>\n\n"
    total = 0
    rows = []

    for cart_item, product in items:
        subtotal = float(product.price) * cart_item.quantity
        total += subtotal
        text += (
            f"• {product.name}\n"
            f"  {cart_item.quantity} × {format_money(product.price)} = {format_money(subtotal)}\n\n"
        )
        rows.append([
            InlineKeyboardButton(text=f"➖ {product.name[:25]}", callback_data=f"cart_dec:{cart_item.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cart_del:{cart_item.id}"),
        ])

    text += f"<b>Итого: {format_money(total)}</b>"

    rows.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout:start")])
    rows.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="cart_clear")])

    await (msg.edit_text if edit else msg.answer)(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


# ─── Изменение количества ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cart_dec:"))
async def cart_decrease(cb: CallbackQuery):
    item_id = cb.data.split(":")[1]
    async with get_session() as db:
        item = await db.get(CartItem, item_id)
        if not item:
            await cb.answer("Товар не найден")
            return
        if item.quantity > 1:
            item.quantity -= 1
        else:
            await db.delete(item)
        await db.commit()
    await cb.answer("Обновлено")
    await _render_cart(cb.message, item.user_id if item else "", edit=True)


@router.callback_query(F.data.startswith("cart_del:"))
async def cart_delete(cb: CallbackQuery):
    item_id = cb.data.split(":")[1]
    user, _ = await get_user_with_org(cb.from_user.id)
    async with get_session() as db:
        item = await db.get(CartItem, item_id)
        if item:
            await db.delete(item)
            await db.commit()
    await cb.answer("Удалено из корзины")
    await _render_cart(cb.message, user.id, edit=True)


@router.callback_query(F.data == "cart_clear")
async def cart_clear(cb: CallbackQuery):
    user, _ = await get_user_with_org(cb.from_user.id)
    async with get_session() as db:
        result = await db.execute(select(CartItem).where(CartItem.user_id == user.id))
        for item in result.scalars().all():
            await db.delete(item)
        await db.commit()
    await cb.answer("Корзина очищена")
    await cb.message.edit_text("Корзина пуста.")


# ─── Оформление заказа ───────────────────────────────────────────────────────

@router.callback_query(F.data == "checkout:start")
async def checkout_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CheckoutStates.comment)
    await cb.message.answer(
        "Введите комментарий к заказу (или отправьте «-» если не нужен):"
    )
    await cb.answer()


@router.message(CheckoutStates.comment)
async def checkout_comment(msg: Message, state: FSMContext):
    comment = msg.text.strip() if msg.text and msg.text != "-" else ""
    await state.clear()

    user, org = await get_user_with_org(msg.from_user.id)
    if not user or not org:
        await msg.answer("Ошибка: пользователь не найден.")
        return

    await msg.answer("Создаю заказ и отправляю в 1С, подождите...")

    onec = make_client()

    async with get_session() as db:
        # Перезагружаем сессии user/org в этой сессии БД
        from sqlalchemy import select
        result = await db.execute(select(type(user)).where(type(user).id == user.id))
        user_db = result.scalar_one()
        org_db = await db.get(type(org), org.id)

        try:
            order = await create_order_from_cart(
                db=db, onec=onec, user=user_db, organization=org_db, comment=comment,
            )
        except OrderCreationError as exc:
            await msg.answer(f"❌ {exc}")
            return

    # ── Отправляем клиенту итоги + PDF документы ──
    text = (
        f"✅ <b>Заказ № {order.invoice_number or order.id[:8]} оформлен</b>\n\n"
        f"Сумма: <b>{format_money(order.total_amount)}</b>\n"
        f"Статус: ожидает оплаты\n\n"
        f"Документы для оплаты прилагаются ниже.\n"
        f"После оплаты по реквизитам в счёте, статус заказа обновится автоматически."
    )
    await msg.answer(text)

    if order.invoice_url:
        try:
            await msg.answer_document(
                URLInputFile(order.invoice_url, filename=f"invoice_{order.invoice_number}.pdf"),
                caption="📄 Счёт на оплату",
            )
        except Exception as exc:
            logger.error("Failed to send invoice PDF: %s", exc)
            await msg.answer(f"Счёт: {order.invoice_url}")

    if order.contract_url:
        try:
            await msg.answer_document(
                URLInputFile(order.contract_url, filename=f"contract_{order.invoice_number}.pdf"),
                caption="📋 Договор",
            )
        except Exception as exc:
            logger.error("Failed to send contract PDF: %s", exc)
            await msg.answer(f"Договор: {order.contract_url}")

"""
Каталог товаров. Навигация по категориям, карточка товара.
Лимиты по уровню клиента отображаются на странице товара.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from sqlalchemy import select

from db import get_session
from models import Category, Product, CartItem
from services.limits import check_can_add_to_cart
from utils import require_active_user, format_money, get_user_with_org

router = Router()
PAGE_SIZE = 8


# ─── Точка входа ──────────────────────────────────────────────────────────────

@router.message(Command("catalog"))
@router.message(F.text == "🛍 Каталог")
async def show_catalog(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return
    await _show_root_categories(msg)


async def _show_root_categories(msg: Message):
    async with get_session() as db:
        result = await db.execute(
            select(Category).where(Category.parent_id.is_(None)).order_by(Category.sort_order, Category.name)
        )
        cats = result.scalars().all()

    if not cats:
        await msg.answer("Категории пока не загружены из 1С.")
        return

    rows = [[InlineKeyboardButton(text=c.name, callback_data=f"cat:{c.id}:0")] for c in cats]
    await msg.answer(
        "Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


# ─── Просмотр категории ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cat:"))
async def show_category(cb: CallbackQuery):
    _, cat_id, page_str = cb.data.split(":")
    page = int(page_str)

    async with get_session() as db:
        # Подкатегории
        sub_result = await db.execute(
            select(Category).where(Category.parent_id == cat_id).order_by(Category.name)
        )
        subs = sub_result.scalars().all()

        # Товары
        prod_result = await db.execute(
            select(Product)
            .where(Product.category_id == cat_id, Product.is_active == True)
            .order_by(Product.name)
            .offset(page * PAGE_SIZE)
            .limit(PAGE_SIZE + 1)
        )
        products = prod_result.scalars().all()
        has_next = len(products) > PAGE_SIZE
        products = products[:PAGE_SIZE]

        category = await db.get(Category, cat_id)

    rows = []

    for s in subs:
        rows.append([InlineKeyboardButton(text=f"📁 {s.name}", callback_data=f"cat:{s.id}:0")])

    for p in products:
        stock = "✅" if p.stock_qty > 0 else "❌"
        rows.append([InlineKeyboardButton(
            text=f"{stock} {p.name[:40]} — {format_money(p.price)}",
            callback_data=f"prod:{p.id}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="« Назад", callback_data=f"cat:{cat_id}:{page-1}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="Далее »", callback_data=f"cat:{cat_id}:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="« К категориям", callback_data="catalog:root")])

    title = category.name if category else "Каталог"
    await cb.message.edit_text(
        f"<b>{title}</b>\n\nСтраница {page + 1}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await cb.answer()


@router.callback_query(F.data == "catalog:root")
async def back_to_root(cb: CallbackQuery):
    async with get_session() as db:
        result = await db.execute(
            select(Category).where(Category.parent_id.is_(None)).order_by(Category.name)
        )
        cats = result.scalars().all()

    rows = [[InlineKeyboardButton(text=c.name, callback_data=f"cat:{c.id}:0")] for c in cats]
    await cb.message.edit_text(
        "Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await cb.answer()


# ─── Карточка товара ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("prod:"))
async def show_product(cb: CallbackQuery):
    prod_id = cb.data.split(":")[1]
    user, org = await get_user_with_org(cb.from_user.id)
    if not user or not org:
        await cb.answer("Сначала зарегистрируйтесь", show_alert=True)
        return

    async with get_session() as db:
        product = await db.get(Product, prod_id)
        if not product or not product.is_active:
            await cb.answer("Товар недоступен", show_alert=True)
            return

        # Проверим лимит чтобы показать клиенту
        limit_check = await check_can_add_to_cart(db, org, product, 1)

    text = (
        f"<b>{product.name}</b>\n\n"
        f"Артикул: <code>{product.sku}</code>\n"
        f"Цена: <b>{format_money(product.price)}</b> / {product.unit}\n"
        f"В наличии: {product.stock_qty} {product.unit}\n"
    )
    if limit_check.max_allowed:
        text += f"\n<i>Доступно для заказа: до {limit_check.max_allowed} {product.unit}</i>"

    rows = []
    if product.stock_qty > 0:
        rows.append([
            InlineKeyboardButton(text="🛒 Добавить 1 шт", callback_data=f"add:{prod_id}:1"),
        ])
        if product.stock_qty >= 5:
            rows.append([
                InlineKeyboardButton(text="+ 5", callback_data=f"add:{prod_id}:5"),
                InlineKeyboardButton(text="+ 10", callback_data=f"add:{prod_id}:10"),
                InlineKeyboardButton(text="+ 50", callback_data=f"add:{prod_id}:50"),
            ])
    rows.append([InlineKeyboardButton(text="« Назад в каталог", callback_data="catalog:root")])

    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await cb.answer()


# ─── Добавление в корзину ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(cb: CallbackQuery):
    _, prod_id, qty_str = cb.data.split(":")
    qty = int(qty_str)

    user, org = await get_user_with_org(cb.from_user.id)
    if not user or not org:
        await cb.answer("Сначала зарегистрируйтесь", show_alert=True)
        return

    async with get_session() as db:
        product = await db.get(Product, prod_id)
        if not product:
            await cb.answer("Товар не найден", show_alert=True)
            return

        # Текущее количество в корзине
        result = await db.execute(
            select(CartItem).where(
                CartItem.user_id == user.id, CartItem.product_id == prod_id,
            )
        )
        existing = result.scalar_one_or_none()
        current_qty = existing.quantity if existing else 0
        new_qty = current_qty + qty

        # Проверка наличия
        if new_qty > product.stock_qty:
            await cb.answer(
                f"Недостаточно на складе. Доступно: {product.stock_qty} {product.unit}",
                show_alert=True,
            )
            return

        # Проверка лимитов
        check = await check_can_add_to_cart(db, org, product, new_qty)
        if not check.ok:
            await cb.answer(check.reason, show_alert=True)
            return

        # Добавляем
        if existing:
            existing.quantity = new_qty
        else:
            db.add(CartItem(user_id=user.id, product_id=prod_id, quantity=qty))
        await db.commit()

    await cb.answer(f"Добавлено в корзину: {qty} {product.unit}")

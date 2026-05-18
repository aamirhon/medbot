"""Утилиты: получение пользователя, проверка статуса, форматирование."""
from sqlalchemy import select
from aiogram.types import Message, CallbackQuery

from db import get_session
from models import User, Organization


async def get_user(telegram_id: int) -> User | None:
    async with get_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def get_user_with_org(telegram_id: int) -> tuple[User | None, Organization | None]:
    async with get_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user or not user.org_id:
            return user, None
        org = await db.get(Organization, user.org_id)
        return user, org


async def require_active_user(event: Message | CallbackQuery) -> User | None:
    """
    Возвращает пользователя если он активен.
    Иначе отправляет сообщение и возвращает None.
    """
    user = await get_user(event.from_user.id)
    target = event.message if isinstance(event, CallbackQuery) else event

    if not user:
        await target.answer("Пожалуйста, начните с команды /start")
        return None
    if user.status == "pending":
        await target.answer("Ваш аккаунт на проверке у администратора.")
        return None
    if user.status == "blocked":
        await target.answer("Ваш аккаунт заблокирован.")
        return None
    return user


def format_money(amount) -> str:
    return f"{float(amount):,.0f} сум".replace(",", " ")


def tier_label(tier: str) -> str:
    return {"vip": "VIP", "standard": "Стандартный", "limited": "Ограниченный"}.get(tier, tier)


def status_label(status: str) -> str:
    return {
        "draft":      "Черновик",
        "pending_1c": "Отправляется в 1С",
        "invoiced":   "Ожидает оплаты",
        "paid":       "Оплачен",
        "shipped":    "Отгружен",
        "delivered":  "Доставлен",
        "cancelled":  "Отменён",
    }.get(status, status)

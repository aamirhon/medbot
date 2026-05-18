"""
Воркер уведомлений: периодически проверяет таблицу OrderEvent
и отправляет push-сообщения клиентам о смене статуса заказа.
"""
import asyncio
import logging

from aiogram import Bot, Router
from sqlalchemy import select

from db import get_session
from models import OrderEvent, Order, User
from utils import status_label, format_money

logger = logging.getLogger(__name__)
router = Router()  # пустой, нужен для совместимости с импортом


async def notifications_loop(bot: Bot):
    while True:
        try:
            await _process_pending(bot)
        except Exception:
            logger.exception("Notifications loop error")
        await asyncio.sleep(20)


async def _process_pending(bot: Bot):
    async with get_session() as db:
        result = await db.execute(
            select(OrderEvent, Order, User)
            .join(Order, Order.id == OrderEvent.order_id)
            .join(User, User.id == Order.user_id)
            .where(OrderEvent.notified == False)
            .limit(50)
        )
        events = result.all()

        for event, order, user in events:
            text = _format_event(event, order)
            if text:
                try:
                    await bot.send_message(user.telegram_id, text)
                except Exception as exc:
                    logger.warning("Не удалось отправить уведомление %s: %s", user.telegram_id, exc)
            event.notified = True

        if events:
            await db.commit()


def _format_event(event: OrderEvent, order: Order) -> str | None:
    title = f"Заказ № {order.invoice_number or order.id[:8]}"
    if event.event_type == "status_changed":
        new_status = event.payload.get("new_status", order.status)
        return f"<b>{title}</b>\n\nНовый статус: {status_label(new_status)}"
    if event.event_type == "payment_received":
        return f"<b>{title}</b>\n\n✅ Оплата получена: {format_money(order.total_amount)}\nЗаказ передан на отгрузку."
    return None

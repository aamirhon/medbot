"""
Точка входа. Запускает бота и параллельно фоновые воркеры синхронизации с 1С.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import settings
from db import init_db
from routers import auth, catalog, cart, orders, staff, notifications
from services import sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    dp.include_router(auth.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(orders.router)
    dp.include_router(staff.router)
    dp.include_router(notifications.router)

    me = await bot.get_me()
    logger.info("Bot started: @%s", me.username)

    # Запускаем бота и воркеры синхронизации параллельно
    await asyncio.gather(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        sync.products_loop(),
        sync.stock_loop(),
        sync.orders_loop(),
        sync.payments_loop(),
        notifications.notifications_loop(bot),
    )


if __name__ == "__main__":
    asyncio.run(main())

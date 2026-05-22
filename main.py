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
# auth must be registered first — it owns /start for both new and existing users.
# main_menu is registered second so its text handlers don't shadow auth's FSM states.
# orders and staff follow; notifications router is empty (loop runs outside aiogram).
from routers import auth, main_menu, orders, staff, notifications
from services import sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    if not settings.WEBAPP_URL.startswith("https://"):
        logger.warning(
            "WEBAPP_URL=%r does not start with https:// — "
            "Telegram will reject the WebApp button. "
            "Set a valid HTTPS URL (ngrok/cloudflared for dev).",
            settings.WEBAPP_URL,
        )

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    dp.include_router(auth.router)
    dp.include_router(main_menu.router)
    dp.include_router(orders.router)
    dp.include_router(staff.router)
    dp.include_router(notifications.router)

    me = await bot.get_me()
    logger.info("Bot started: @%s", me.username)

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

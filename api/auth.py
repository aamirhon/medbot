"""
Авторизация через Telegram WebApp.

В режиме разработки (DEV_MODE=true в .env) — авторизация по test_telegram_id
из заголовка X-Dev-Telegram-Id. Это позволяет тестировать API через Swagger
и Mini App в браузере без реального Telegram.
"""
import hashlib
import hmac
import json
import logging
import os
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status
from sqlalchemy import select

from config import settings
from db import get_session
from models import User

logger = logging.getLogger(__name__)

MAX_INIT_DATA_AGE_SECONDS = 24 * 60 * 60
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


def verify_telegram_init_data(init_data: str) -> dict:
    """Проверяет HMAC-подпись initData и возвращает user_data."""
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        raise HTTPException(401, "Invalid initData format")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Missing hash in initData")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > MAX_INIT_DATA_AGE_SECONDS:
        raise HTTPException(401, "initData expired")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(
        b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(401, "Invalid initData signature")

    user_json = parsed.get("user")
    if not user_json:
        raise HTTPException(401, "User not in initData")

    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        raise HTTPException(401, "Invalid user JSON")


async def get_current_user(
    x_telegram_init_data: str = Header("", alias="X-Telegram-Init-Data"),
    x_dev_telegram_id: str = Header("", alias="X-Dev-Telegram-Id"),
) -> User:
    """
    Извлекает пользователя из заголовков.

    Production: проверяет подпись X-Telegram-Init-Data.
    Dev:        принимает X-Dev-Telegram-Id (если DEV_MODE=true).
    """
    telegram_id: int | None = None

    if x_telegram_init_data:
        tg_user = verify_telegram_init_data(x_telegram_init_data)
        telegram_id = int(tg_user.get("id", 0)) or None

    if not telegram_id and DEV_MODE and x_dev_telegram_id:
        try:
            telegram_id = int(x_dev_telegram_id)
            logger.warning("DEV MODE: using telegram_id=%s without verification", telegram_id)
        except ValueError:
            pass

    if not telegram_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Authentication required",
        )

    async with get_session() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Не зарегистрированы. Откройте бота и пройдите регистрацию по ИНН.",
        )
    if user.status != "active":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Аккаунт в статусе {user.status}",
        )
    return user

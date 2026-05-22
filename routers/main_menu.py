"""
Post-registration hub.

Exports:
  build_main_menu_kb(lang) — ReplyKeyboardMarkup with WebApp button + nav buttons.
  send_main_menu(msg, user, org) — greeting + keyboard, used by auth.py after registration.

Handles:
  🌐 Язык / 🌐 Til    → inline language switcher + /language command
  ℹ️ Помощь / Yordam   → static help text
  📞 Контакты / Kontaktlar → static contacts text
"""
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, WebAppInfo,
)
from sqlalchemy import select

from config import settings
from db import get_session
from i18n import t
from models import Organization, User
from utils import require_active_user

logger = logging.getLogger(__name__)
router = Router()

# Label sets used for F.text.in_() matchers — computed once at import time.
_LANGUAGE_LABELS = frozenset({t("menu.language", "ru"), t("menu.language", "uz")})
_HELP_LABELS     = frozenset({t("menu.help",     "ru"), t("menu.help",     "uz")})
_CONTACT_LABELS  = frozenset({t("menu.contacts", "ru"), t("menu.contacts", "uz")})


# ─── Public helpers ───────────────────────────────────────────────────────────

def build_main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    if settings.WEBAPP_URL.startswith("https://"):
        catalog_btn = KeyboardButton(
            text=t("menu.catalog", lang),
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    else:
        # WEBAPP_URL not configured yet — plain button so the rest of the menu works.
        catalog_btn = KeyboardButton(text=t("menu.catalog", lang))

    return ReplyKeyboardMarkup(
        keyboard=[
            [catalog_btn],
            [
                KeyboardButton(text=t("menu.orders",   lang)),
                KeyboardButton(text=t("menu.language", lang)),
            ],
            [
                KeyboardButton(text=t("menu.help",     lang)),
                KeyboardButton(text=t("menu.contacts", lang)),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def send_main_menu(msg: Message, user: User, org: Organization | None) -> None:
    lang = user.language or "ru"
    org_name = org.name if org else (user.first_name or "")
    await msg.answer(
        t("greeting", lang, organization_name=org_name),
        reply_markup=build_main_menu_kb(lang),
    )


# ─── Help ─────────────────────────────────────────────────────────────────────

@router.message(F.text.in_(_HELP_LABELS))
async def handle_help(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return
    await msg.answer(t("help_text", user.language or "ru"))


# ─── Contacts ─────────────────────────────────────────────────────────────────
# TODO: replace locales/{ru,uz}.json "contacts_text" with real contact details.

@router.message(F.text.in_(_CONTACT_LABELS))
async def handle_contacts(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return
    await msg.answer(t("contacts_text", user.language or "ru"))


# ─── Language switcher ────────────────────────────────────────────────────────

@router.message(Command("language"))
@router.message(F.text.in_(_LANGUAGE_LABELS))
async def handle_language(msg: Message):
    user = await require_active_user(msg)
    if not user:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("language.ru_btn", "ru"), callback_data="lang:ru"),
        InlineKeyboardButton(text=t("language.uz_btn", "ru"), callback_data="lang:uz"),
    ]])
    await msg.answer(t("language.prompt", user.language or "ru"), reply_markup=kb)


@router.callback_query(F.data.startswith("lang:"))
async def set_language(cb: CallbackQuery):
    new_lang = cb.data.split(":")[1]
    if new_lang not in ("ru", "uz"):
        await cb.answer()
        return

    async with get_session() as db:
        result = await db.execute(select(User).where(User.telegram_id == cb.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            await cb.answer()
            return
        user.language = new_lang
        org = await db.get(Organization, user.org_id) if user.org_id else None
        await db.commit()

    await cb.answer()

    org_name = org.name if org else (cb.from_user.first_name or "")
    await cb.message.answer(
        t("language.changed", new_lang) + "\n\n" + t("greeting", new_lang, organization_name=org_name),
        reply_markup=build_main_menu_kb(new_lang),
    )

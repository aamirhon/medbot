"""
Регистрация: клиент вводит ИНН → бот проверяет в 1С →
если найден, подтягивает данные → создаёт User + Organization.
"""
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from config import settings
from db import get_session
from keyboards import confirm_kb
from models import User, Organization
from routers.main_menu import build_main_menu_kb, send_main_menu
from services.onec_client import Client1C, ClientNotFound, OneCError
from services.sync import make_client
from utils import get_user_with_org

logger = logging.getLogger(__name__)
router = Router()


class RegStates(StatesGroup):
    inn     = State()
    confirm = State()


@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    user, org = await get_user_with_org(msg.from_user.id)

    if user and user.status == "active":
        await send_main_menu(msg, user, org)
        return

    if user and user.status == "pending":
        await msg.answer(
            "Ваша заявка на проверке у администратора.\n"
            "Как только организация будет верифицирована, "
            "вы получите уведомление."
        )
        return

    await state.set_state(RegStates.inn)
    await msg.answer(
        "Добро пожаловать!\n\n"
        "Для работы введите ИНН вашей организации (9 или 12 цифр):",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(RegStates.inn)
async def step_inn(msg: Message, state: FSMContext):
    inn = (msg.text or "").strip().replace(" ", "")

    if not inn.isdigit() or len(inn) not in (9, 12):
        await msg.answer("ИНН должен содержать 9 или 12 цифр. Попробуйте ещё раз:")
        return

    async with get_session() as db:
        from sqlalchemy import select
        result = await db.execute(select(Organization).where(Organization.inn == inn))
        existing_org = result.scalar_one_or_none()

        if existing_org and existing_org.status == "active":
            user = User(
                telegram_id=msg.from_user.id,
                first_name=msg.from_user.first_name or "",
                last_name=msg.from_user.last_name or "",
                role="client",
                org_id=existing_org.id,
                status="active",
                language="ru",
            )
            db.add(user)
            await db.commit()
            await state.clear()
            await msg.answer(
                f"Добавили вас в организацию {existing_org.name}.",
                reply_markup=build_main_menu_kb("ru"),
            )
            return

    await msg.answer("Проверяю в 1С...")
    onec: Client1C = make_client()

    try:
        info = await onec.check_client_by_inn(inn)
    except ClientNotFound:
        await msg.answer(
            "Организация с таким ИНН не найдена в нашей системе.\n\n"
            "Проверьте правильность ИНН и попробуйте ещё раз "
            "или свяжитесь с менеджером:\n"
            "📞 +998 XX XXX-XX-XX\n\n"
            "Введите ИНН (9 или 12 цифр):"
        )
        return
    except OneCError as exc:
        logger.error("1С недоступна при проверке ИНН %s: %s", inn, exc)
        await msg.answer(
            "Сейчас не удалось связаться с 1С. Попробуйте через минуту.\n\n"
            "Введите ИНН ещё раз:"
        )
        return

    await state.update_data(
        inn=inn,
        one_c_id=info["one_c_id"],
        name=info["name"],
        tier=info.get("tier", "standard"),
        phone=info.get("phone", ""),
        address=info.get("address", ""),
        type=info.get("type", "clinic"),
    )
    await state.set_state(RegStates.confirm)

    summary = (
        "Найдена организация:\n\n"
        f"<b>{info['name']}</b>\n"
        f"ИНН: <code>{inn}</code>\n"
    )
    if info.get("phone"):
        summary += f"Телефон: {info['phone']}\n"
    if info.get("address"):
        summary += f"Адрес: {info['address']}\n"
    summary += "\nПодтверждаете регистрацию?"

    await msg.answer(summary, reply_markup=confirm_kb())


@router.message(RegStates.confirm, F.text == "Подтвердить")
async def step_confirm(msg: Message, state: FSMContext):
    data = await state.get_data()

    async with get_session() as db:
        org = Organization(
            inn=data["inn"],
            name=data["name"],
            type=data.get("type", "clinic"),
            phone=data.get("phone", ""),
            address=data.get("address", ""),
            one_c_id=data["one_c_id"],
            client_tier=data["tier"],
            status="active",
        )
        db.add(org)
        await db.flush()

        is_admin = msg.from_user.id in settings.admin_ids
        user = User(
            telegram_id=msg.from_user.id,
            first_name=msg.from_user.first_name or "",
            last_name=msg.from_user.last_name or "",
            role="admin" if is_admin else "client",
            org_id=org.id,
            status="active",
            language="ru",
        )
        db.add(user)
        await db.commit()

    await state.clear()

    # Уровень клиентам не показываем — только ограниченным даём подсказку
    if org.client_tier == "limited":
        welcome = (
            "Регистрация завершена.\n\n"
            "По вашему аккаунту есть ограничения. "
            "Для уточнения деталей свяжитесь с менеджером:\n"
            "📞 +998 XX XXX-XX-XX\n\n"
            "Используйте меню ниже для работы с каталогом."
        )
    else:
        welcome = (
            "Регистрация завершена.\n\n"
            "Используйте меню ниже для работы с каталогом."
        )

    await msg.answer(welcome, reply_markup=build_main_menu_kb("ru"))


@router.message(RegStates.confirm, F.text == "Отмена")
async def step_cancel(msg: Message, state: FSMContext):
    await state.set_state(RegStates.inn)
    await msg.answer(
        "Хорошо, давайте попробуем ещё раз.\n\n"
        "Введите ИНН вашей организации (9 или 12 цифр):",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text == "👤 Профиль")
async def show_profile(msg: Message):
    from utils import get_user_with_org
    user, org = await get_user_with_org(msg.from_user.id)
    if not user or not org:
        await msg.answer("Пожалуйста, начните с /start")
        return

    text = (
        f"<b>{org.name}</b>\n\n"
        f"ИНН: <code>{org.inn}</code>\n"
        f"Тип: {'Госучреждение' if org.type == 'government' else 'Частная клиника'}\n"
    )
    if org.phone:
        text += f"Телефон: {org.phone}\n"

    if org.client_tier == "limited":
        text += (
            f"\n\n<i>По вашему аккаунту есть ограничения. "
            f"Для уточнения свяжитесь с менеджером.</i>"
        )

    await msg.answer(text)

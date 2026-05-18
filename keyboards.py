from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb(role: str = "client") -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="📋 Мои заказы"), KeyboardButton(text="👤 Профиль")],
    ]
    if role in ("staff", "accountant", "admin"):
        rows.append([KeyboardButton(text="⚙️ Панель сотрудника")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def confirm_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Подтвердить"), KeyboardButton(text="Отмена")]],
        resize_keyboard=True,
    )

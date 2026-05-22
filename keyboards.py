from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def confirm_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Подтвердить"), KeyboardButton(text="Отмена")]],
        resize_keyboard=True,
    )

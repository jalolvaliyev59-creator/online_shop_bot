from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import settings


def get_main_menu(user_id: int = None):
    keyboard = [
        [KeyboardButton(text="🛍️ Katalog"), KeyboardButton(text="🛒 Savatcha")],
        [KeyboardButton(text="📞 Biz bilan bog'lanish")]
    ]
    if user_id and user_id in settings.ADMIN_IDS:
        keyboard.append([KeyboardButton(text="👨‍💼 Admin panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
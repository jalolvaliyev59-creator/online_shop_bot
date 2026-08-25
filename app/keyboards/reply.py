from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🛍 Katalog"), KeyboardButton(text="🛒 Savatcha")],
        [KeyboardButton(text="📦 Buyurtmalarim"), KeyboardButton(text="📞 Biz bilan bog'lanish")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="🛠 Admin Panel")])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    """
    Bazadan kelgan kategoriyalar ro'yxati asosida inline tugmalar yasaydi.
    categories - bu obyektlar yoki so'zlar ro'yxati bo'lishi mumkin.
    """
    keyboard = []
    
    for category in categories:
        # Har bir kategoriya uchun tugma yaratamiz
        # category.id va category.name bazadagi ustun nomlari bo'ladi
        keyboard.append([
            InlineKeyboardButton(
                text=category.name, 
                callback_data=f"category_{category.id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_products_keyboard(products: list) -> InlineKeyboardMarkup:
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product.name} - {product.price} so'm", 
                callback_data=f"product_{product.id}"
            )
        ])
    # Orqaga qaytish tugmasi
    keyboard.append([InlineKeyboardButton(text="⬅️ Kategoriyalarga qaytish", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
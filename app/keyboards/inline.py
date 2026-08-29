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

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_products_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    # Mahsulot tugmalari...
    
    # Orqaga qaytish tugmasini qo'shamiz
    keyboard.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_categories"))
    return keyboard

from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_shop_menu_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Oldindan bor bo'lgan tugmalaringiz (masalan):
    builder.button(text="🛍 Katalog", callback_data="catalog")
    builder.button(text="🛒 Savatcha", callback_data="cart")
    builder.button(text="📦 Buyurtmalarim", callback_data="my_orders")
    
    # ⬇️ Mana shu yerga "Fikr bildirish" tugmasini qo'shasiz:
    builder.button(text="💬 Fikr bildirish", callback_data="leave_feedback")
    
    builder.adjust(2) # Tugmalar qatoriga nechta chiqishini belgilaydi
    return builder.as_markup()
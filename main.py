import asyncio
import logging
import sys

from app.handlers.admin import admin_router
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, 
    CallbackQuery, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# O'zimizning modullardan importlar
from app.database.connection import init_db
from app.database.requests import (
    add_initial_categories,
    add_initial_products,
    get_categories,
    get_products_by_category,
    get_product_by_id,
    add_to_cart,
    get_user_cart,
    clear_cart,
    create_order_from_cart
)
from app.states.order import OrderState


TOKEN = "8556213613:AAEOZK0z00EFftvY9R7Th9tUMCT7_361YLA"

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

# Asosiy menyu tugmalari (ReplyKeyboardMarkup)
def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Katalog"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="📞 Biz bilan bog'lanish")]
        ],
        resize_keyboard=True
    )

# 1. /start komandasi
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n"
        "Online-do'konimiz botiga xush kelibsiz. Kerakli bo'limni tanlang:",
        reply_markup=get_main_menu()
    )

# 2. Katalog tugmasi bosilganda
@dp.message(F.text == "🛍️ Katalog")
async def show_categories(message: Message) -> None:
    categories = await get_categories()
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
            for cat in categories
        ]
    )
    await message.answer("Kategoriyalardan birini tanlang:", reply_markup=keyboard)

# 3. Kategoriya tanlanganda mahsulotlarni ko'rsatish
@dp.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery) -> None:
    category_id = int(callback.data.split("_")[1])
    products = await get_products_by_category(category_id)
    
    if not products:
        await callback.answer("Bu kategoriyada hozircha mahsulot yo'q.", show_alert=True)
        return
        
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{prod.name} - {prod.price} so'm", callback_data=f"prod_{prod.id}")]
            for prod in products
        ]
    )
    await callback.message.edit_text("Mahsulotlardan birini tanlang:", reply_markup=keyboard)
    await callback.answer()

# 4. Mahsulot tafsilotlari
@dp.callback_query(F.data.startswith("prod_"))
async def show_product_detail(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split("_")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Mahsulot topilmadi.", show_alert=True)
        return
        
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Savatchaga qo'shish", callback_data=f"add_cart_{product.id}")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"cat_{product.category_id}")]
        ]
    )
    
    text = f"<b>{product.name}</b>\n\nNarxi: {product.price} so'm\nTavsif: {product.description}"
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# 5. Savatchaga qo'shish
@dp.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    await add_to_cart(user_id, product_id)
    await callback.answer("Mahsulot savatchaga qo'shildi! ✅", show_alert=False)

# 6. Savatcha tugmasi bosilganda
@dp.message(F.text == "🛒 Savatcha")
async def show_cart(message: Message) -> None:
    user_id = message.from_user.id
    cart_items = await get_user_cart(user_id)
    
    if not cart_items:
        await message.answer("Savatchangiz bo'sh. 📭")
        return
        
    total_sum = 0
    text = "<b>Sizning savatchangiz:</b>\n\n"
    
    for cart, product in cart_items:
        sum_price = product.price * cart.quantity
        total_sum += sum_price
        text += f"• {product.name} x {cart.quantity} = {sum_price} so'm\n"
        
    text += f"\n<b>Umumiy summa: {total_sum} so'm</b>"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="create_order")],
            [InlineKeyboardButton(text="🗑️ Savatchani tozalash", callback_data="clear_cart")]
        ]
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# 7. Savatchani tozalash
@dp.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery) -> None:
    await clear_cart(callback.from_user.id)
    await callback.message.edit_text("Savatchangiz tozalandi. 🗑️")
    await callback.answer()

# ==========================================
# BUYURTMA BERISH VA FSM (HOLATLAR) QISMI
# ==========================================

# A) Buyurtma berish boshlanishi (Telefon raqamni so'rash)
@dp.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id
    
    cart_items = await get_user_cart(user_id)
    if not cart_items:
        await callback.answer("Savatchangiz bo'sh!", show_alert=True)
        return
        
    await state.set_state(OrderState.phone)
    
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await callback.message.answer(
        "📱 Buyurtmani rasmiylashtirish uchun telefon raqamingizni yuboring (pastdagi tugmani bosing yoki yozib yuboring):",
        reply_markup=phone_keyboard
    )
    await callback.answer()

# B) Telefon raqamni qabul qilish va manzilni so'rash
@dp.message(OrderState.phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else message.text
    
    await state.update_data(phone=phone)
    await state.set_state(OrderState.address)
    
    await message.answer(
        "📍 Endi yetkazib berish manzilini yuboring (masalan: Shahar, ko'cha, uy raqami):",
        reply_markup=ReplyKeyboardRemove()
    )

# C) Manzilni qabul qilish va bazaga saqlash
@dp.message(OrderState.address)
async def process_address(message: Message, state: FSMContext) -> None:
    address = message.text
    data = await state.get_data()
    phone = data.get("phone")
    user_id = message.from_user.id
    
    # Bazaga buyurtma qo'shamiz
    order_id = await create_order_from_cart(user_id=user_id, phone=phone, address=address)
    
    await state.clear()
    
    if not order_id:
        await message.answer("Xatolik yuz berdi. Savatchangiz bo'sh bo'lishi mumkin.", reply_markup=get_main_menu())
        return
        
    await message.answer(
        f"🎉 <b>Buyurtmangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🆔 Buyurtma raqami: #{order_id}\n"
        f"📞 Telefon: {phone}\n"
        f"📍 Manzil: {address}\n\n"
        f"Tez orada operatorlarimiz siz bilan bog'lanishadi. 🚀",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

# Botni ishga tushirish
async def main():
    # Bazani yaratish va boshlang'ich ma'lumotlarni qo'shish
    await init_db()
    await add_initial_categories()
    await add_initial_products()
    
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
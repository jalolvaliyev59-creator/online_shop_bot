from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config import settings
from app.database.requests import get_categories, add_product
from app.states.admin import AddProduct

admin_router = Router()

# Admin ekanligini tekshiruvchi filter
@admin_router.message(F.text == "👨‍💼 Admin panel")
async def admin_panel(message: Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Sizda bu bo'limga kirish huquqi yo'q! ❌")
        return
        
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    await message.answer("Admin panelga xush kelibsiz! Kerakli amalni tanlang:", reply_markup=keyboard)

# 1. Mahsulot qo'shishni boshlash (Kategoriyalarni ko'rsatish)
@admin_router.message(F.text == "➕ Mahsulot qo'shish")
async def start_add_product(message: Message, state: FSMContext):
    if message.from_user.id not in settings.ADMIN_IDS:
        return
        
    categories = await get_categories()
    if not categories:
        await message.answer("Avval kategoriyalar yaratilishi kerak!")
        return
        
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"adm_cat_{cat.id}")]
            for cat in categories
        ]
    )
    await message.state.set_state(AddProduct.category) if hasattr(message, "state") else None
    # Yuqoridagi o'rniga to'g'ridan-to'g'ri state'ni o'rnatamiz:
    await state.set_state(AddProduct.category)
    await message.answer("Mahsulot qaysi kategoriyaga tegishli? Tanlang:", reply_markup=keyboard)

# 2. Kategoriyani qabul qilib, nomini so'rash
@admin_router.callback_query(AddProduct.category, F.data.startswith("adm_cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split("_")[2]
    await state.update_data(category_id=category_id)
    
    await state.set_state(AddProduct.name)
    await callback.message.answer("Yangi mahsulot nomini kiriting:")
    await callback.answer()

# 3. Nomini qabul qilib, tavsifini so'rash
@admin_router.message(AddProduct.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Mahsulot haqida qisqacha tavsif (description) kiriting:")

# 4. Tavsifni qabul qilib, narxini so'rash
@admin_router.message(AddProduct.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Mahsulot narxini kiriting (faqat raqamlarda, masalan: 1200000):")

# 5. Narxni qabul qilib, bazaga saqlash
@admin_router.message(AddProduct.price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, narxni faqat raqamlarda kiriting!")
        return
        
    await state.update_data(price=message.text)
    data = await state.get_data()
    
    # Bazaga qo'shamiz
    await add_product(data)
    await state.clear()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    await message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=keyboard)
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import settings

admin_router = Router()

# Faqat ADMIN_IDS dagi foydalanuvchilar kira olishi uchun filter
@admin_router.message(Command("admin"), F.from_user.id.in_(settings.ADMIN_IDS))
async def admin_main(message: Message):
    await message.answer(
        "👨‍💼 **Admin panelga xush kelibsiz!**\n\nKerakli amalni tanlang:",
        reply_markup=admin_keyboard() # Admin tugmalari
    )
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup,
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from config import settings
from app.database.requests import (
    get_categories, add_product, add_category,
    get_all_products, delete_product,
    get_all_orders, update_order_status
)
from app.states.admin import AddProduct, AddCategory
from app.keyboards.reply import get_main_menu

admin_router = Router()


def admin_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📋 Mahsulotlar")],
            [KeyboardButton(text="📁 Kategoriya qo'shish"), KeyboardButton(text="🛒 Buyurtmalar")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )


@admin_router.message(F.text == "👨‍💼 Admin panel")
async def admin_panel(message: Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        await message.answer("Sizda bu bo'limga kirish huquqi yo'q! ❌")
        return
    await message.answer(
        "👨‍💼 Admin panelga xush kelibsiz!\n\nKerakli amalni tanlang:",
        reply_markup=admin_menu_keyboard()
    )


@admin_router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu(message.from_user.id))


# ================= MAHSULOT QO'SHISH =================

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
    await state.set_state(AddProduct.category)
    await message.answer("Mahsulot qaysi kategoriyaga tegishli? Tanlang:", reply_markup=keyboard)


@admin_router.callback_query(AddProduct.category, F.data.startswith("adm_cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AddProduct.name)
    await callback.message.answer("Yangi mahsulot nomini kiriting:")
    await callback.answer()


@admin_router.message(AddProduct.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Mahsulot haqida qisqacha tavsif kiriting:")


@admin_router.message(AddProduct.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Mahsulot narxini kiriting (faqat raqamlarda, masalan: 1200000):")


@admin_router.message(AddProduct.price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, narxni faqat raqamlarda kiriting!")
        return

    await state.update_data(price=int(message.text))
    data = await state.get_data()
    await add_product(data)
    await state.clear()

    await message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=admin_menu_keyboard())


# ================= KATEGORIYA QO'SHISH =================

@admin_router.message(F.text == "📁 Kategoriya qo'shish")
async def start_add_category(message: Message, state: FSMContext):
    if message.from_user.id not in settings.ADMIN_IDS:
        return
    await state.set_state(AddCategory.name)
    await message.answer("Yangi kategoriya nomini kiriting:")


@admin_router.message(AddCategory.name)
async def process_category_name(message: Message, state: FSMContext):
    await add_category(message.text)
    await state.clear()
    await message.answer(f"✅ '{message.text}' kategoriyasi qo'shildi!", reply_markup=admin_menu_keyboard())


# ================= MAHSULOTLAR RO'YXATI (O'CHIRISH) =================

@admin_router.message(F.text == "📋 Mahsulotlar")
async def list_products(message: Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        return

    products = await get_all_products()
    if not products:
        await message.answer("Hozircha mahsulotlar yo'q.")
        return

    for product in products:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_prod_{product.id}")]
            ]
        )
        text = f"📦 <b>{product.name}</b>\nNarxi: {product.price} so'm\nQoldiq: {product.quantity}"
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@admin_router.callback_query(F.data.startswith("del_prod_"))
async def delete_product_handler(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    await delete_product(product_id)
    await callback.message.edit_text("🗑 Mahsulot o'chirildi.")
    await callback.answer()


# ================= BUYURTMALAR =================

STATUS_OPTIONS = ["Yangi", "Tayyorlanmoqda", "Yetkazilmoqda", "Yetkazildi", "Bekor qilindi"]


@admin_router.message(F.text == "🛒 Buyurtmalar")
async def list_orders(message: Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        return

    orders = await get_all_orders()
    if not orders:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return

    for order in orders[:10]:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=status, callback_data=f"ordstat_{order.id}_{status}")]
                for status in STATUS_OPTIONS
            ]
        )
        text = (
            f"🆔 Buyurtma #{order.id}\n"
            f"💰 Summa: {order.total_price} so'm\n"
            f"📞 Telefon: {order.phone}\n"
            f"📍 Manzil: {order.delivery_address}\n"
            f"📌 Holat: {order.status}"
        )
        await message.answer(text, reply_markup=keyboard)


@admin_router.callback_query(F.data.startswith("ordstat_"))
async def change_order_status(callback: CallbackQuery):
    parts = callback.data.split("_")
    order_id = int(parts[1])
    new_status = parts[2]
    await update_order_status(order_id, new_status)
    await callback.answer(f"Holat yangilandi: {new_status}", show_alert=True)
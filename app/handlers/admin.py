from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup,
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from app.database.requests import (
    get_shop_by_owner, get_categories, add_product, add_category,
    get_all_products, delete_product,
    get_all_orders, update_order_status,
    update_product_price, update_product_quantity,
    add_promocode, get_shop_stats
)
from app.states.admin import AddProduct, AddCategory, EditProduct, AddPromocode

admin_router = Router()

MENU_TEXTS = {
    "➕ Mahsulot qo'shish", "📋 Mahsulotlar", "📁 Kategoriya qo'shish", "📦 Buyurtmalar",
    "🎟 Promokod qo'shish", "📊 Statistika"
}


def admin_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📋 Mahsulotlar")],
            [KeyboardButton(text="📁 Kategoriya qo'shish"), KeyboardButton(text="📦 Buyurtmalar")],
            [KeyboardButton(text="🎟 Promokod qo'shish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🛍️ Mijoz sifatida ko'rish")]
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


async def get_owner_shop(telegram_id: int):
    return await get_shop_by_owner(telegram_id)


# ================= HAR QANDAY HOLATDA MENYU TUGMASI BOSILSA — BEKOR QILISH =================

@admin_router.message(F.text.in_(MENU_TEXTS | {"❌ Bekor qilish"}))
async def cancel_any_state(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        if message.text == "❌ Bekor qilish":
            await message.answer("Bekor qilindi.", reply_markup=admin_menu_keyboard())
            return
    await route_menu_text(message, state)


async def route_menu_text(message: Message, state: FSMContext):
    shop = await get_owner_shop(message.from_user.id)
    if not shop:
        return

    if message.text == "➕ Mahsulot qo'shish":
        await start_add_product(message, state, shop)
    elif message.text == "📋 Mahsulotlar":
        await list_products(message, shop)
    elif message.text == "📁 Kategoriya qo'shish":
        await start_add_category(message, state)
    elif message.text == "📦 Buyurtmalar":
        await list_orders(message, shop)
    elif message.text == "🎟 Promokod qo'shish":
        await start_add_promocode(message, state)
    elif message.text == "📊 Statistika":
        await show_shop_stats(message, shop)

# ================= MAHSULOT QO'SHISH =================

async def start_add_product(message: Message, state: FSMContext, shop):
    categories = await get_categories(shop.id)
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
    await callback.message.answer("Yangi mahsulot nomini kiriting:", reply_markup=cancel_keyboard())
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

    shop = await get_owner_shop(message.from_user.id)
    if not shop:
        await state.clear()
        return

    await state.update_data(price=int(message.text))
    data = await state.get_data()

    await add_product(data, shop.id)
    await state.clear()

    await message.answer("✅ Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=admin_menu_keyboard())


# ================= KATEGORIYA QO'SHISH =================

async def start_add_category(message: Message, state: FSMContext):
    await state.set_state(AddCategory.name)
    await message.answer("Yangi kategoriya nomini kiriting:", reply_markup=cancel_keyboard())


@admin_router.message(AddCategory.name)
async def process_category_name(message: Message, state: FSMContext):
    shop = await get_owner_shop(message.from_user.id)
    if not shop:
        await state.clear()
        return

    await add_category(message.text, shop.id)
    await state.clear()
    await message.answer(f"✅ '{message.text}' kategoriyasi qo'shildi!", reply_markup=admin_menu_keyboard())


# ================= MAHSULOTLAR RO'YXATI (O'CHIRISH / TAHRIRLASH) =================

async def list_products(message: Message, shop):
    products = await get_all_products(shop.id)
    if not products:
        await message.answer("Hozircha mahsulotlar yo'q.")
        return

    for product in products:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💰 Narxni o'zgartirish", callback_data=f"edit_price_{product.id}"),
                    InlineKeyboardButton(text="📦 Qoldiqni o'zgartirish", callback_data=f"edit_qty_{product.id}")
                ],
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


@admin_router.callback_query(F.data.startswith("edit_price_"))
async def start_edit_price(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProduct.price)
    await callback.message.answer("Yangi narxni kiriting (faqat raqamlarda):", reply_markup=cancel_keyboard())
    await callback.answer()


@admin_router.message(EditProduct.price)
async def process_edit_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    data = await state.get_data()
    await update_product_price(data["product_id"], int(message.text))
    await state.clear()
    await message.answer("✅ Narx yangilandi!", reply_markup=admin_menu_keyboard())


@admin_router.callback_query(F.data.startswith("edit_qty_"))
async def start_edit_qty(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)
    await state.set_state(EditProduct.quantity)
    await callback.message.answer("Yangi qoldiq miqdorini kiriting:", reply_markup=cancel_keyboard())
    await callback.answer()


@admin_router.message(EditProduct.quantity)
async def process_edit_qty(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    data = await state.get_data()
    await update_product_quantity(data["product_id"], int(message.text))
    await state.clear()
    await message.answer("✅ Qoldiq yangilandi!", reply_markup=admin_menu_keyboard())


# ================= BUYURTMALAR =================

STATUS_OPTIONS = {
    "1": "Yangi",
    "2": "Tayyorlanmoqda",
    "3": "Yetkazilmoqda",
    "4": "Yetkazildi",
    "5": "Bekor qilindi"
}


async def list_orders(message: Message, shop):
    orders = await get_all_orders(shop.id)
    if not orders:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return

    for order in orders[:10]:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=status_name, callback_data=f"ordstat_{order.id}_{status_id}")]
                for status_id, status_name in STATUS_OPTIONS.items()
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
    status_id = parts[2]
    
    new_status = STATUS_OPTIONS.get(status_id)
    if not new_status:
        await callback.answer("Xatolik yuz berdi!", show_alert=True)
        return

    await update_order_status(order_id, new_status)
    await callback.answer(f"Holat yangilandi: {new_status}", show_alert=True)
    
    try:
        old_text = callback.message.text
        updated_text = "\n".join(
            [f"📌 Holat: {new_status}" if line.startswith("📌 Holat:") else line for line in old_text.split("\n")]
        )
        await callback.message.edit_text(updated_text, reply_markup=callback.message.reply_markup)
    except Exception:
        pass


# ================= PROMOKOD =================

async def start_add_promocode(message: Message, state: FSMContext):
    await state.set_state(AddPromocode.code)
    await message.answer("Promokod nomini kiriting (masalan: WELCOME10):", reply_markup=cancel_keyboard())


@admin_router.message(AddPromocode.code)
async def process_promocode_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text)
    await state.set_state(AddPromocode.discount)
    await message.answer("Chegirma foizini kiriting (masalan: 10):")


@admin_router.message(AddPromocode.discount)
async def process_promocode_discount(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 100):
        await message.answer("Iltimos, 1 dan 100 gacha bo'lgan raqam kiriting!")
        return

    shop = await get_owner_shop(message.from_user.id)
    if not shop:
        await state.clear()
        return

    data = await state.get_data()
    await add_promocode(shop.id, data["code"], int(message.text))
    await state.clear()
    await message.answer(f"✅ Promokod qo'shildi: {data['code'].upper()} — {message.text}% chegirma", reply_markup=admin_menu_keyboard())


# ================= STATISTIKA =================

async def show_shop_stats(message: Message, shop):
    stats = await get_shop_stats(shop.id)
    text = (
        f"📊 <b>«{shop.name}» statistikasi</b>\n\n"
        f"📦 Jami mahsulotlar: {stats['total_products']}\n"
        f"🛒 Jami buyurtmalar: {stats['total_orders']}\n"
        f"💰 Jami tushum: {stats['total_revenue']} so'm"
    )
    await message.answer(text, parse_mode="HTML")
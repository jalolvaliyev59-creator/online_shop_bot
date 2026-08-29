import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ErrorEvent
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from sqlalchemy import select

from config import settings
from app.database.connection import init_db, async_session
from app.middlewares.throttling import ThrottlingMiddleware
from app.handlers.admin import admin_router
from app.states.order import OrderState
from app.states.admin import AddShop

from app.models.shop import Shop
from app.models.feedback import Feedback

from app.database.requests import (
    search_products,
    get_user_orders,
    update_cart_quantity,
    get_cart_item_by_id,
    toggle_wishlist,
    get_wishlist,
    get_shop_by_code,
    get_shop_by_id,
    get_all_shops,
    create_shop,
    set_current_shop,
    get_current_shop_id,
    get_categories,
    get_products_by_category,
    get_product_by_id,
    add_to_cart,
    get_user_cart,
    clear_cart,
    create_order_from_cart,
    get_last_address
)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()

dp.message.middleware(ThrottlingMiddleware())
dp.callback_query.middleware(ThrottlingMiddleware())

dp.include_router(router)

@dp.errors()
async def global_error_handler(event: ErrorEvent):
    logging.exception(f"Xatolik yuz berdi: {event.exception}")
    try:
        if event.update.message:
            await event.update.message.answer("⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qayta urinib ko'ring yoki /start bosing.")
        elif event.update.callback_query:
            await event.update.callback_query.answer("⚠️ Xatolik yuz berdi, qayta urinib ko'ring.", show_alert=True)
    except Exception:
        pass
    return True


# ================= YORDAMCHI FUNKSIYALAR =================

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Katalog"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="🔍 Qidiruv"), KeyboardButton(text="📦 Buyurtmalarim")],
            [KeyboardButton(text="❤️ Sevimlilar"), KeyboardButton(text="📞 Biz bilan bog'lanish")]
        ],
        resize_keyboard=True
    )

def is_super_admin(telegram_id: int) -> bool:
    return telegram_id in settings.ADMIN_IDS


async def get_active_shop_id(telegram_id: int):
    return await get_current_shop_id(telegram_id)


# ================= /start (asosiy kirish nuqtasi) =================

import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ErrorEvent
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from sqlalchemy import select

from config import settings
from app.database.connection import init_db, async_session
from app.middlewares.throttling import ThrottlingMiddleware
from app.handlers.admin import admin_router
from app.states.order import OrderState
from app.states.admin import AddShop

from app.models.shop import Shop
from app.models.feedback import Feedback

from app.database.requests import (
    search_products,
    get_user_orders,
    update_cart_quantity,
    get_cart_item_by_id,
    toggle_wishlist,
    get_wishlist,
    get_shop_by_code,
    get_shop_by_id,
    get_all_shops,
    create_shop,
    set_current_shop,
    get_current_shop_id,
    get_categories,
    get_products_by_category,
    get_product_by_id,
    add_to_cart,
    get_user_cart,
    clear_cart,
    create_order_from_cart,
    get_last_address
)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()

dp.message.middleware(ThrottlingMiddleware())
dp.callback_query.middleware(ThrottlingMiddleware())
dp.include_router(admin_router)
dp.include_router(router)

@dp.errors()
async def global_error_handler(event: ErrorEvent):
    logging.exception(f"Xatolik yuz berdi: {event.exception}")
    try:
        if event.update.message:
            await event.update.message.answer("⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qayta urinib ko'ring yoki /start bosing.")
        elif event.update.callback_query:
            await event.update.callback_query.answer("⚠️ Xatolik yuz berdi, qayta urinib ko'ring.", show_alert=True)
    except Exception:
        pass
    return True


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Katalog"), KeyboardButton(text="🛒 Savatcha")],
            [KeyboardButton(text="🔍 Qidiruv"), KeyboardButton(text="📦 Buyurtmalarim")],
            [KeyboardButton(text="❤️ Sevimlilar"), KeyboardButton(text="📞 Biz bilan bog'lanish")]
        ],
        resize_keyboard=True
    )

def shop_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📋 Mahsulotlar")],
            [KeyboardButton(text="📁 Kategoriya qo'shish"), KeyboardButton(text="📦 Buyurtmalar")],
            [KeyboardButton(text="🎟 Promokod qo'shish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🛍️ Mijoz sifatida ko'rish")]
        ],
        resize_keyboard=True
    )

def super_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Do'konlar ro'yxati")],
            [KeyboardButton(text="➕ Yangi do'kon yaratish")]
        ],
        resize_keyboard=True
    )

def is_super_admin(telegram_id: int) -> bool:
    return telegram_id in settings.ADMIN_IDS

async def get_active_shop_id(telegram_id: int):
    return await get_current_shop_id(telegram_id)


@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.from_user.id
    
    # O'z Telegram IDingizni shu yerga yozing (avtomatik admin bo'lib kirishi uchun)
    MY_TELEGRAM_ID = 8556213613  # Botingizdagi ID yoki o'z ID raqamingiz
    
    if telegram_id == MY_TELEGRAM_ID or is_super_admin(telegram_id):
        # Agar bazada do'kon bo'lmasa, avtomatik bitta do'kon yaratib qo'yamiz
        async with async_session() as session:
            result = await session.execute(select(Shop).where(Shop.owner_id == telegram_id))
            shop = result.scalar_one_or_none()
            if not shop:
                shop = Shop(name="Mening Do'konim", owner_id=telegram_id, start_code=f"shop{telegram_id}")
                session.add(shop)
                await session.commit()
            await set_current_shop(telegram_id, shop.id)
            
        await message.answer(
            "👨‍💼 Assalomu alaykum! Siz do'kon egasisiz.\n\nAdmin panel:",
            reply_markup=shop_admin_menu(),
            parse_mode="HTML"
        )
        return

    start_code = command.args
    if start_code:
        shop = await get_shop_by_code(start_code)
        if not shop:
            await message.answer("❌ Bunday do'kon topilmadi. Havola noto'g'ri bo'lishi mumkin.")
            return

        await set_current_shop(telegram_id, shop.id)
        if shop.owner_id == telegram_id:
            await message.answer(
                f"👨‍💼 Assalomu alaykum! Siz <b>{shop.name}</b> do'konining egasisiz.",
                reply_markup=shop_admin_menu(),
                parse_mode="HTML"
            )
            return

        await message.answer(
            f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
            f"🏪 <b>{shop.name}</b> do'koniga xush kelibsiz!\nKerakli bo'limni tanlang:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Do'konga kirish uchun havoladan foydalaning yoki /start buyrug'ini bosing."
    )


# Katalog, savatcha va buyurtma funksiyalari
@dp.message(F.text == "🛍️ Katalog")
async def show_categories(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, do'konni tanlang.")
        return

    categories = await get_categories(shop_id)
    if not categories:
        await message.answer("Hozircha kategoriyalar yo'q.")
        return

    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.name, callback_data=f"cat_{cat.id}")
    builder.button(text="🔍 Mahsulot qidirish", callback_data="start_search")
    builder.button(text="💬 Fikr bildirish", callback_data="leave_feedback")
    builder.adjust(1)
    
    await message.answer("Kategoriyalardan birini tanlang:", reply_markup=builder.as_markup())


@dp.message(F.text == "🛒 Savatcha")
async def show_cart_v2(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, do'konni tanlang.")
        return

    cart_items = await get_user_cart(message.from_user.id, shop_id)
    if not cart_items:
        await message.answer("Savatchangiz bo'sh. 📭")
        return

    total_sum = 0
    keyboard_rows = []
    for cart, product in cart_items:
        sum_price = product.price * cart.quantity
        total_sum += sum_price
        keyboard_rows.append([
            InlineKeyboardButton(text=f"➖", callback_data=f"cartminus_{cart.id}"),
            InlineKeyboardButton(text=f"{product.name} x{cart.quantity}", callback_data="noop"),
            InlineKeyboardButton(text=f"➕", callback_data=f"cartplus_{cart.id}"),
        ])

    keyboard_rows.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="start_order")])
    keyboard_rows.append([InlineKeyboardButton(text="🗑️ Savatchani tozalash", callback_data="clear_cart")])

    text = f"<b>Sizning savatchangiz:</b>\n\n💰 Umumiy summa: {total_sum} so'm"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="HTML")


@dp.message(F.text == "🛍️ Mijoz sifatida ko'rish")
async def switch_to_customer_view(message: Message) -> None:
    await message.answer(
        "🛍️ Mijoz rejimi yoqildi.",
        reply_markup=get_main_menu()
    )


async def handle_ping(request):
    return web.Response(text="Bot is alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await init_db()
    print("Bot muvaffaqiyatli ishga tushdi!")
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

# ================= BOSH ADMIN PANELI =================

def super_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Do'konlar ro'yxati")],
            [KeyboardButton(text="➕ Yangi do'kon yaratish")]
        ],
        resize_keyboard=True
    )


@dp.message(F.text == "🏪 Do'konlar ro'yxati")
async def list_shops(message: Message):
    if not is_super_admin(message.from_user.id):
        return

    shops = await get_all_shops()
    if not shops:
        await message.answer("Hozircha do'konlar yo'q.")
        return

    text = "🏪 <b>Barcha do'konlar:</b>\n\n"
    for shop in shops:
        text += f"🔹 <b>{shop.name}</b>\n   Egasi ID: {shop.owner_id}\n   Havola: t.me/{(await bot.get_me()).username}?start={shop.start_code}\n\n"
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "➕ Yangi do'kon yaratish")
async def start_create_shop(message: Message, state: FSMContext):
    if not is_super_admin(message.from_user.id):
        return
    await state.set_state(AddShop.name)
    await message.answer("Yangi do'konning nomini kiriting:")


@dp.message(AddShop.name)
async def process_shop_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddShop.owner_id)
    await message.answer("Do'kon egasining Telegram ID raqamini kiriting:")


@dp.message(AddShop.owner_id)
async def process_shop_owner(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    data = await state.get_data()
    owner_id = int(message.text)
    start_code = f"shop{owner_id}"

    shop = await create_shop(name=data["name"], owner_id=owner_id, start_code=start_code)
    await state.clear()

    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={shop.start_code}"

    await message.answer(
        f"✅ Do'kon yaratildi!\n\n"
        f"🏪 Nomi: {shop.name}\n"
        f"👤 Egasi ID: {shop.owner_id}\n"
        f"🔗 Havola: {link}\n\n"
        f"Shu havolani do'kon egasiga yuboring.",
        reply_markup=super_admin_menu()
    )


# ================= DO'KON EGASI ADMIN PANELI =================

def shop_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📋 Mahsulotlar")],
            [KeyboardButton(text="📁 Kategoriya qo'shish"), KeyboardButton(text="📦 Buyurtmalar")],
            [KeyboardButton(text="🎟 Promokod qo'shish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🛍️ Mijoz sifatida ko'rish")]
        ],
        resize_keyboard=True
    )


# ================= MIJOZ: KATALOG VA KATEGORIYALAR =================

@dp.message(F.text == "🛍️ Katalog")
async def show_categories(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return

    categories = await get_categories(shop_id)
    if not categories:
        await message.answer("Hozircha kategoriyalar yo'q.")
        return

    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.name, callback_data=f"cat_{cat.id}")
    builder.button(text="🔍 Mahsulot qidirish", callback_data="start_search")
    builder.button(text="💬 Fikr bildirish", callback_data="leave_feedback")
    builder.adjust(1)
    
    await message.answer("Kategoriyalardan birini tanlang:", reply_markup=builder.as_markup())


PRODUCTS_PER_PAGE = 5

def build_products_keyboard(products, category_id, page):
    total_pages = (len(products) - 1) // PRODUCTS_PER_PAGE + 1
    start = page * PRODUCTS_PER_PAGE
    end = start + PRODUCTS_PER_PAGE
    page_products = products[start:end]

    keyboard = [
        [InlineKeyboardButton(text=f"{prod.name} - {prod.price} so'm", callback_data=f"prod_{prod.id}")]
        for prod in page_products
    ]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"catpage_{category_id}_{page - 1}"))
    if end < len(products):
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"catpage_{category_id}_{page + 1}"))
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton(text="🔙 Kategoriyalarga qaytish", callback_data="back_to_categories")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard), total_pages


@router.callback_query(F.data.startswith("cat_"))
async def show_products(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    category_id = int(callback.data.split("_")[1])
    products = await get_products_by_category(category_id, shop_id)

    if not products:
        await callback.answer("Bu kategoriyada hozircha mahsulot yo'q.", show_alert=True)
        return

    keyboard, total_pages = build_products_keyboard(products, category_id, page=0)
    text = f"Mahsulotlardan birini tanlang: (1/{total_pages}-sahifa)"
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("catpage_"))
async def show_products_page(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    parts = callback.data.split("_")
    category_id = int(parts[1])
    page = int(parts[2])
    products = await get_products_by_category(category_id, shop_id)

    if not products:
        await callback.answer("Mahsulot topilmadi.", show_alert=True)
        return

    keyboard, total_pages = build_products_keyboard(products, category_id, page=page)
    text = f"Mahsulotlardan birini tanlang: ({page + 1}/{total_pages}-sahifa)"
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    categories = await get_categories(shop_id)
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat.name, callback_data=f"cat_{cat.id}")
    builder.button(text="🔍 Mahsulot qidirish", callback_data="start_search")
    builder.button(text="💬 Fikr bildirish", callback_data="leave_feedback")
    builder.adjust(1)
    
    await callback.message.edit_text("Kategoriyalardan birini tanlang:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def show_product_detail(callback: CallbackQuery) -> None:
    product_id = int(callback.data.split("_")[1])
    product = await get_product_by_id(product_id)

    if not product:
        await callback.answer("Mahsulot topilmadi.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Savatchaga qo'shish", callback_data=f"add_cart_{product.id}")],
            [InlineKeyboardButton(text="❤️ Sevimlilarga qo'shish/olib tashlash", callback_data=f"wish_{product.id}")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"cat_{product.category_id}")]
        ]
    )
    text = f"<b>{product.name}</b>\n\nNarxi: {product.price} so'm\nTavsif: {product.description}"
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("wish_"))
async def wishlist_toggle_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    product_id = int(callback.data.split("_")[1])
    added = await toggle_wishlist(callback.from_user.id, product_id, shop_id)
    if added:
        await callback.answer("❤️ Sevimlilarga qo'shildi!", show_alert=False)
    else:
        await callback.answer("Sevimlilardan olib tashlandi.", show_alert=False)


@dp.message(F.text == "❤️ Sevimlilar")
async def show_wishlist(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return
    items = await get_wishlist(message.from_user.id, shop_id)
    if not items:
        await message.answer("Sevimlilar ro'yxati bo'sh. ❤️")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{product.name} - {product.price} so'm", callback_data=f"prod_{product.id}")]
            for wish, product in items
        ]
    )
    await message.answer("❤️ Sizning sevimlilaringiz:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    product_id = int(callback.data.split("_")[2])
    await add_to_cart(callback.from_user.id, product_id, shop_id)
    await callback.answer("Mahsulot savatchaga qo'shildi! ✅", show_alert=False)


# ================= MIJOZ: SAVAT =================

@dp.message(F.text == "🛒 Savatcha")
async def show_cart_v2(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return

    cart_items = await get_user_cart(message.from_user.id, shop_id)
    if not cart_items:
        await message.answer("Savatchangiz bo'sh. 📭")
        return

    total_sum = 0
    keyboard_rows = []
    for cart, product in cart_items:
        sum_price = product.price * cart.quantity
        total_sum += sum_price
        keyboard_rows.append([
            InlineKeyboardButton(text=f"➖", callback_data=f"cartminus_{cart.id}"),
            InlineKeyboardButton(text=f"{product.name} x{cart.quantity}", callback_data="noop"),
            InlineKeyboardButton(text=f"➕", callback_data=f"cartplus_{cart.id}"),
        ])

    keyboard_rows.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="start_order")])
    keyboard_rows.append([InlineKeyboardButton(text="🗑️ Savatchani tozalash", callback_data="clear_cart")])

    text = f"<b>Sizning savatchangiz:</b>\n\n💰 Umumiy summa: {total_sum} so'm"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="HTML")


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("cartplus_"))
async def cart_plus(callback: CallbackQuery) -> None:
    cart_id = int(callback.data.split("_")[1])
    item = await get_cart_item_by_id(cart_id)
    if not item:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    cart, product = item
    await update_cart_quantity(cart_id, cart.quantity + 1)
    await refresh_cart_message(callback)


@router.callback_query(F.data.startswith("cartminus_"))
async def cart_minus(callback: CallbackQuery) -> None:
    cart_id = int(callback.data.split("_")[1])
    item = await get_cart_item_by_id(cart_id)
    if not item:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    cart, product = item
    await update_cart_quantity(cart_id, cart.quantity - 1)
    await refresh_cart_message(callback)


async def refresh_cart_message(callback: CallbackQuery):
    shop_id = await get_active_shop_id(callback.from_user.id)
    cart_items = await get_user_cart(callback.from_user.id, shop_id)

    if not cart_items:
        await callback.message.edit_text("Savatchangiz bo'sh. 📭")
        await callback.answer()
        return

    total_sum = 0
    keyboard_rows = []
    for cart, product in cart_items:
        sum_price = product.price * cart.quantity
        total_sum += sum_price
        keyboard_rows.append([
            InlineKeyboardButton(text=f"➖", callback_data=f"cartminus_{cart.id}"),
            InlineKeyboardButton(text=f"{product.name} x{cart.quantity}", callback_data="noop"),
            InlineKeyboardButton(text=f"➕", callback_data=f"cartplus_{cart.id}"),
        ])

    keyboard_rows.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="start_order")])
    keyboard_rows.append([InlineKeyboardButton(text="🗑️ Savatchani tozalash", callback_data="clear_cart")])

    text = f"<b>Sizning savatchangiz:</b>\n\n💰 Umumiy summa: {total_sum} so'm"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    await clear_cart(callback.from_user.id, shop_id)
    await callback.message.edit_text("Savatchangiz tozalandi. 🗑️")
    await callback.answer()


# ================= BUYURTMA VA MANZIL =================

@router.callback_query(F.data == "start_order")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    shop_id = data.get("current_shop_id") or await get_active_shop_id(callback.from_user.id)
    user_id = callback.from_user.id
    
    cart_items = await get_user_cart(user_id, shop_id)
    if not cart_items:
        await callback.answer("Savatchangiz bo'sh!", show_alert=True)
        return

    phone, last_address = await get_last_address(user_id, shop_id)
    
    if last_address and phone:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Ha, shu manzildan foydalanish", callback_data="use_last_address")
        builder.button(text="✍️ Yangi manzil kiritish", callback_data="enter_new_address")
        builder.adjust(1)
        
        await state.update_data(saved_phone=phone, saved_address=last_address, current_shop_id=shop_id)
        
        await callback.message.answer(
            f"📍 Sizning oxirgi manzilingiz topildi:\n\n"
            f"📞 Tel: <b>{phone}</b>\n"
            f"🏠 Manzil: <b>{last_address}</b>\n\n"
            f"Shu manzilga yetkazib beraylikmi?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    else:
        await state.update_data(current_shop_id=shop_id)
        await state.set_state(OrderState.phone)
        await callback.message.answer(
            "📞 Iltimos, aloqa uchun telefon raqamingizni yuboring (masalan: +998901234567):",
            reply_markup=ReplyKeyboardRemove()
        )
    await callback.answer()


@router.callback_query(F.data == "use_last_address")
async def use_saved_address(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    phone = data.get("saved_phone")
    address = data.get("saved_address")
    shop_id = data.get("current_shop_id") or await get_active_shop_id(callback.from_user.id)
    telegram_id = callback.from_user.id

    order_id, total_price, items_summary = await create_order_from_cart_detailed(telegram_id, shop_id, phone, address)
    await state.clear()

    if not order_id:
        await callback.message.answer("❌ Xatolik yuz berdi. Buyurtma yaratilmadi.", reply_markup=get_main_menu())
        return

    await notify_shop_owner(bot, shop_id, order_id, telegram_id, phone, address, total_price, items_summary)

    await callback.message.answer(
        f"🎉 <b>Buyurtmangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🆔 Buyurtma raqami: #{order_id}\n"
        f"📞 Tel: {phone}\n"
        f"🏠 Manzil: {address}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "enter_new_address")
async def enter_new_address(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.phone)
    await callback.message.answer(
        "📞 Iltimos, telefon raqamingizni yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()


@router.message(OrderState.phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else message.text
    digits = "".join(filter(str.isdigit, phone))
    
    if len(digits) < 9:
        await message.answer("❗️ Telefon raqami noto'g'ri. Iltimos, masalan: +998901234567 ko'rinishida to'g'ri raqam yuboring.")
        return
        
    await state.update_data(phone=phone)
    await state.set_state(OrderState.address)
    await message.answer("📍 Endi yetkazib berish manzilini yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(OrderState.address)
async def process_address(message: Message, state: FSMContext) -> None:
    address = message.text
    data = await state.get_data()
    phone = data.get("phone")
    telegram_id = message.from_user.id
    shop_id = data.get("current_shop_id") or await get_active_shop_id(telegram_id)

    order_id, total_price, items_summary = await create_order_from_cart_detailed(telegram_id, shop_id, phone, address)
    await state.clear()

    if not order_id:
        await message.answer("❌ Xatolik yuz berdi.", reply_markup=get_main_menu())
        return

    await notify_shop_owner(bot, shop_id, order_id, telegram_id, phone, address, total_price, items_summary)

    await message.answer(
        f"🎉 <b>Buyurtmangiz muvaffaqiyatli qabul qilindi!</b>\n\n🆔 Buyurtma raqami: #{order_id}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


async def create_order_from_cart_detailed(user_id: int, shop_id: int, phone: str, address: str):
    cart_items = await get_user_cart(user_id, shop_id)
    if not cart_items:
        return None, 0, ""

    total_price = 0
    items_lines = []
    for cart, product in cart_items:
        sum_price = product.price * cart.quantity
        total_price += sum_price
        items_lines.append(f"• {product.name} x{cart.quantity} — {sum_price:,} so'm")

    items_text = "\n".join(items_lines)
    order_id = await create_order_from_cart(user_id=user_id, shop_id=shop_id, phone=phone, address=address)
    return order_id, total_price, items_text


async def notify_shop_owner(bot: Bot, shop_id: int, order_id: int, user_id: int, phone: str, address: str, total_price: int, items_text: str):
    async with async_session() as session:
        result = await session.execute(select(Shop).where(Shop.id == shop_id))
        shop = result.scalar_one_or_none()
        
    if shop and shop.owner_telegram_id:
        try:
            text = (
                f"🚨 <b>Yangi buyurtma! №{order_id}</b>\n\n"
                f"🛍 Do'kon: <b>{shop.name}</b>\n"
                f"👤 Xaridor ID: <code>{user_id}</code>\n"
                f"📞 Telefon: <b>{phone}</b>\n"
                f"📍 Manzil: <b>{address}</b>\n\n"
                f"📦 <b>Mahsulotlar:</b>\n{items_text}\n\n"
                f"💰 <b>Jami summa:</b> {total_price:,} so'm"
            )
            
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Qabul qilish", callback_data=f"accept_order_{order_id}")
            builder.button(text="❌ Bekor qilish", callback_data=f"cancel_order_{order_id}")
            builder.adjust(2)
            
            await bot.send_message(
                shop.owner_telegram_id, 
                text, 
                parse_mode="HTML", 
                reply_markup=builder.as_markup()
            )
        except Exception:
            pass


# ================= FIKR BILDIRISH (FEEDBACK) TIZIMI =================

class FeedbackState(StatesGroup):
    waiting_text = State()

@router.callback_query(F.data == "leave_feedback")
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    shop_id = await get_active_shop_id(callback.from_user.id)
    await state.update_data(current_shop_id=shop_id)
    await state.set_state(FeedbackState.waiting_text)
    await callback.message.answer("✍️ Do'kon haqida o'z fikringiz, shikoyat yoki taklifingizni shu yerga yozib qoldiring:")
    await callback.answer()

@router.message(FeedbackState.waiting_text)
async def save_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    shop_id = data.get("current_shop_id") or await get_active_shop_id(message.from_user.id)
    
    if not shop_id:
        await message.answer("❌ Xatolik yuz berdi. Iltimos, do'konga qaytadan kiring.")
        await state.clear()
        return

    async with async_session() as session:
        fb = Feedback(
            shop_id=shop_id, 
            user_id=message.from_user.id, 
            text=message.text.strip()
        )
        session.add(fb)
        await session.commit()
        
        result = await session.execute(select(Shop).where(Shop.id == shop_id))
        shop = result.scalar_one_or_none()

    if shop and shop.owner_telegram_id:
        try:
            user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
            await message.bot.send_message(
                shop.owner_telegram_id,
                f"💬 <b>«{shop.name}» do'koningizga yangi fikr keldi!</b>\n\n"
                f"👤 Xaridor: {user_info}\n"
                f"📝 Xabar: {message.text.strip()}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await message.answer("✅ Fikringiz uchun rahmat! U bevosita do'kon egasiga yetkazildi.")
    await state.clear()


# ================= QIDIRUV (SEARCH) =================

class SearchState(StatesGroup):
    query = State()

@router.callback_query(F.data == "start_search")
async def start_product_search(callback: CallbackQuery, state: FSMContext):
    shop_id = await get_active_shop_id(callback.from_user.id)
    await state.update_data(current_shop_id=shop_id)
    await state.set_state(SearchState.query)
    await callback.message.answer("🔍 Qidirilayotgan mahsulot nomini yozing:")
    await callback.answer()

@dp.message(F.text == "🔍 Qidiruv")
async def start_search_menu(message: Message, state: FSMContext) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return
    await state.update_data(current_shop_id=shop_id)
    await state.set_state(SearchState.query)
    await message.answer("🔍 Qidirilayotgan mahsulot nomini yozing:")


@router.message(SearchState.query)
async def process_search(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    shop_id = data.get("current_shop_id") or await get_active_shop_id(message.from_user.id)
    await state.clear()

    results = await search_products(shop_id, message.text)
    if not results:
        await message.answer("Hech narsa topilmadi. 😔", reply_markup=get_main_menu())
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{p.name} - {p.price} so'm", callback_data=f"prod_{p.id}")]
            for p in results[:15]
        ]
    )
    await message.answer(f"🔍 Topildi ({len(results)} ta):", reply_markup=keyboard)


# ================= BIZ BILAN BOG'LANISH VA BUYURTMALARIM =================

@dp.message(F.text == "📞 Biz bilan bog'lanish")
async def contact_handler(message: Message) -> None:
    await message.answer("📞 Biz bilan bog'lanish uchun do'kon ma'muriyatiga murojaat qiling.")


@dp.message(F.text == "📦 Buyurtmalarim")
async def show_my_orders(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return

    orders = await get_user_orders(message.from_user.id, shop_id)
    if not orders:
        await message.answer("Sizda hali buyurtmalar yo'q.")
        return

    text = "📦 <b>Sizning buyurtmalaringiz:</b>\n\n"
    for order in orders[:10]:
        text += f"🆔 #{order.id} — {order.total_price} so'm — {order.status}\n"
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "🛍️ Mijoz sifatida ko'rish")
async def switch_to_customer_view(message: Message) -> None:
    await message.answer(
        "🛍️ Endi mijoz rejimidasiz. Katalogni ko'rishingiz mumkin.\n\n"
        "Admin panelga qaytish uchun /start buyrug'ini bosing.",
        reply_markup=get_main_menu()
    )


# ================= WEB SERVER (Render uchun) =================

async def handle_ping(request):
    return web.Response(text="Bot is alive")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# ================= ISHGA TUSHIRISH =================

async def main():
    await init_db()
    print("Bot ishga tushdi...")
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())



# Eski qismni o'rniga shuni qo'ying:

async def main():
    await init_db()
    print("Bot muvaffaqiyatli ishga tushdi!")
    await start_web_server()
    
    # Event loop xatoligini oldini olish uchun botni shu yerda ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi!")
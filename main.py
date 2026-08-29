import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from app.handlers.admin import admin_router
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
from app.database.requests import (
    search_products,
    get_user_orders,
    update_cart_quantity,
    get_cart_item_by_id
)

from aiogram.types import ErrorEvent
from config import settings
from app.database.connection import init_db
from app.database.requests import (
    get_shop_by_code,
    get_shop_by_owner,
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
    create_order_from_cart
)
from app.states.order import OrderState
from app.states.admin import AddShop

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
from app.middlewares.throttling import ThrottlingMiddleware

dp.message.middleware(ThrottlingMiddleware())
dp.callback_query.middleware(ThrottlingMiddleware())
dp.include_router(admin_router)
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
            [KeyboardButton(text="📞 Biz bilan bog'lanish")]
        ],
        resize_keyboard=True
    )

def is_super_admin(telegram_id: int) -> bool:
    return telegram_id in settings.ADMIN_IDS


async def get_active_shop_id(telegram_id: int):
    """Foydalanuvchining hozir qaysi do'konda ekanini aniqlaydi."""
    return await get_current_shop_id(telegram_id)


# ================= /start (asosiy kirish nuqtasi) =================

@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.from_user.id
    start_code = command.args  # ?start=shop1 bo'lsa "shop1" keladi

    if start_code:
        shop = await get_shop_by_code(start_code)
        if not shop:
            await message.answer("❌ Bunday do'kon topilmadi. Havola noto'g'ri bo'lishi mumkin.")
            return

        # Do'kon egasimi?
        if shop.owner_id == telegram_id:
            await message.answer(
                f"👨‍💼 Assalomu alaykum! Siz <b>{shop.name}</b> do'konining egasisiz.\n\nAdmin panelga xush kelibsiz!",
                reply_markup=shop_admin_menu(),
                parse_mode="HTML"
            )
            return

        # Oddiy mijoz — shu do'konga biriktiramiz
        await set_current_shop(telegram_id, shop.id)
        await message.answer(
            f"Assalomu alaykum, {message.from_user.first_name}!\n\n"
            f"🏪 <b>{shop.name}</b> do'koniga xush kelibsiz!\nKerakli bo'limni tanlang:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return

    # Linksiz oddiy /start
    if is_super_admin(telegram_id):
        await message.answer(
            "👑 Assalomu alaykum, bosh admin!\n\nKerakli amalni tanlang:",
            reply_markup=super_admin_menu()
        )
        return

    # Mijoz — avvalgi do'koniga qaytishga urinamiz
    shop_id = await get_active_shop_id(telegram_id)
    if shop_id:
        shop = await get_shop_by_id(shop_id)
        if shop:
            await message.answer(
                f"Xush kelibsiz, {message.from_user.first_name}!\n\n"
                f"🏪 <b>{shop.name}</b>\nKerakli bo'limni tanlang:",
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
            return

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Bu bot faqat do'kon havolasi orqali ishlaydi. "
        "Iltimos, sizga berilgan do'kon havolasidan (masalan t.me/BotName?start=shop1) kiring."
    )


# ================= BOSH ADMIN PANELI (barcha do'konlar) =================

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
            [KeyboardButton(text="📁 Kategoriya qo'shish"), KeyboardButton(text="📦 Buyurtmalar")]
        ],
        resize_keyboard=True
    )


# ================= MIJOZ: KATALOG =================

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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
            for cat in categories
        ]
    )
    await message.answer("Kategoriyalardan birini tanlang:", reply_markup=keyboard)


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


@dp.callback_query(F.data.startswith("cat_"))
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


@dp.callback_query(F.data.startswith("catpage_"))
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


@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    categories = await get_categories(shop_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
            for cat in categories
        ]
    )
    await callback.message.edit_text("Kategoriyalardan birini tanlang:", reply_markup=keyboard)
    await callback.answer()


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


@dp.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    product_id = int(callback.data.split("_")[2])
    await add_to_cart(callback.from_user.id, product_id, shop_id)
    await callback.answer("Mahsulot savatchaga qo'shildi! ✅", show_alert=False)


# ================= MIJOZ: SAVAT =================

@dp.message(F.text == "🛒 Savatcha")
async def show_cart(message: Message) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return

    cart_items = await get_user_cart(message.from_user.id, shop_id)
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


@dp.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    await clear_cart(callback.from_user.id, shop_id)
    await callback.message.edit_text("Savatchangiz tozalandi. 🗑️")
    await callback.answer()


# ================= BUYURTMA (FSM) =================

@dp.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext) -> None:
    shop_id = await get_active_shop_id(callback.from_user.id)
    cart_items = await get_user_cart(callback.from_user.id, shop_id)
    if not cart_items:
        await callback.answer("Savatchangiz bo'sh!", show_alert=True)
        return

    await state.set_state(OrderState.phone)
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.answer(
        "📱 Buyurtmani rasmiylashtirish uchun telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard
    )
    await callback.answer()


@dp.message(OrderState.phone, F.contact | F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    await state.set_state(OrderState.address)
    await message.answer(
        "📍 Endi yetkazib berish manzilini yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(OrderState.address)
async def process_address(message: Message, state: FSMContext) -> None:
    address = message.text
    data = await state.get_data()
    phone = data.get("phone")
    telegram_id = message.from_user.id
    shop_id = await get_active_shop_id(telegram_id)

    order_id = await create_order_from_cart(user_id=telegram_id, shop_id=shop_id, phone=phone, address=address)
    await state.clear()

    if not order_id:
        await message.answer("Xatolik yuz berdi.", reply_markup=get_main_menu())
        return

    await message.answer(
        f"🎉 <b>Buyurtmangiz muvaffaqiyatli qabul qilindi!</b>\n\n🆔 Buyurtma raqami: #{order_id}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@dp.message(F.text == "📞 Biz bilan bog'lanish")
async def contact_handler(message: Message) -> None:
    await message.answer("📞 Biz bilan bog'lanish uchun admin bilan bog'laning.")


# ================= QIDIRUV =================

class SearchState:
    from aiogram.fsm.state import State, StatesGroup

    class Search(StatesGroup):
        query = State()


@dp.message(F.text == "🔍 Qidiruv")
async def start_search(message: Message, state: FSMContext) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
    if not shop_id:
        await message.answer("Iltimos, avval do'kon havolasi orqali kiring.")
        return
    await state.set_state(SearchState.Search.query)
    await message.answer("Qidirilayotgan mahsulot nomini yozing:")


@dp.message(SearchState.Search.query)
async def process_search(message: Message, state: FSMContext) -> None:
    shop_id = await get_active_shop_id(message.from_user.id)
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


# ================= BUYURTMALARIM =================

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


# ================= SAVATNI +/- BILAN TAHRIRLASH =================

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

    keyboard_rows.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="create_order")])
    keyboard_rows.append([InlineKeyboardButton(text="🗑️ Savatchani tozalash", callback_data="clear_cart")])

    text = f"<b>Sizning savatchangiz:</b>\n\n💰 Umumiy summa: {total_sum} so'm"
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="HTML")


@dp.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery) -> None:
    await callback.answer()


@dp.callback_query(F.data.startswith("cartplus_"))
async def cart_plus(callback: CallbackQuery) -> None:
    cart_id = int(callback.data.split("_")[1])
    item = await get_cart_item_by_id(cart_id)
    if not item:
        await callback.answer("Topilmadi.", show_alert=True)
        return
    cart, product = item
    await update_cart_quantity(cart_id, cart.quantity + 1)
    await refresh_cart_message(callback)


@dp.callback_query(F.data.startswith("cartminus_"))
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

    keyboard_rows.append([InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="create_order")])
    keyboard_rows.append([InlineKeyboardButton(text="🗑️ Savatchani tozalash", callback_data="clear_cart")])

    text = f"<b>Sizning savatchangiz:</b>\n\n💰 Umumiy summa: {total_sum} so'm"
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_rows), parse_mode="HTML")
    await callback.answer()


# ================= WEB SERVER (Render uchun) =================

from aiohttp import web


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
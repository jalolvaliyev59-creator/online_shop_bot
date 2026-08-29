from sqlalchemy import select
from app.database.connection import async_session
from app.models.product import Category, Product
from app.models.cart import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.shop import Shop
from app.models.session import UserSession


# ================= DO'KON (SHOP) =================

async def get_shop_by_code(start_code: str):
    async with async_session() as session:
        result = await session.execute(select(Shop).where(Shop.start_code == start_code))
        return result.scalars().first()


async def get_shop_by_owner(owner_id: int):
    async with async_session() as session:
        result = await session.execute(select(Shop).where(Shop.owner_id == owner_id))
        return result.scalars().first()


async def get_shop_by_id(shop_id: int):
    async with async_session() as session:
        result = await session.execute(select(Shop).where(Shop.id == shop_id))
        return result.scalars().first()


async def get_all_shops():
    async with async_session() as session:
        result = await session.execute(select(Shop))
        return result.scalars().all()


async def create_shop(name: str, owner_id: int, start_code: str):
    async with async_session() as session:
        shop = Shop(name=name, owner_id=owner_id, start_code=start_code)
        session.add(shop)
        await session.commit()
        await session.refresh(shop)
        return shop


# ================= FOYDALANUVCHI SESSIYASI (qaysi do'konda turibdi) =================

async def set_current_shop(telegram_id: int, shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(UserSession).where(UserSession.telegram_id == telegram_id)
        )
        session_obj = result.scalars().first()
        if session_obj:
            session_obj.current_shop_id = shop_id
        else:
            session_obj = UserSession(telegram_id=telegram_id, current_shop_id=shop_id)
            session.add(session_obj)
        await session.commit()


async def get_current_shop_id(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(UserSession).where(UserSession.telegram_id == telegram_id)
        )
        session_obj = result.scalars().first()
        return session_obj.current_shop_id if session_obj else None


# ================= KATEGORIYALAR =================

async def get_categories(shop_id: int):
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.shop_id == shop_id))
        return result.scalars().all()


async def add_category(name: str, shop_id: int):
    async with async_session() as session:
        session.add(Category(name=name, shop_id=shop_id))
        await session.commit()


# ================= MAHSULOTLAR =================

async def get_products_by_category(category_id: int, shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.category_id == category_id, Product.shop_id == shop_id)
        )
        return result.scalars().all()


async def get_product_by_id(product_id: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalars().first()


async def get_all_products(shop_id: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.shop_id == shop_id))
        return result.scalars().all()


async def add_product(data: dict, shop_id: int):
    async with async_session() as session:
        product = Product(
            name=data["name"],
            description=data["description"],
            price=int(data["price"]),
            category_id=int(data["category_id"]),
            shop_id=shop_id
        )
        session.add(product)
        await session.commit()


async def delete_product(product_id: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if product:
            await session.delete(product)
            await session.commit()


# ================= SAVAT =================

async def add_to_cart(user_id: int, product_id: int, shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
                CartItem.shop_id == shop_id
            )
        )
        cart_item = result.scalars().first()

        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=user_id, product_id=product_id, shop_id=shop_id, quantity=1)
            session.add(cart_item)

        await session.commit()


async def get_user_cart(user_id: int, shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.user_id == user_id, CartItem.shop_id == shop_id)
        )
        return result.all()


async def clear_cart(user_id: int, shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(CartItem).where(CartItem.user_id == user_id, CartItem.shop_id == shop_id)
        )
        items = result.scalars().all()
        for item in items:
            await session.delete(item)
        await session.commit()


# ================= BUYURTMALAR =================

async def create_order_from_cart(user_id: int, shop_id: int, phone: str, address: str):
    async with async_session() as session:
        result = await session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.user_id == user_id, CartItem.shop_id == shop_id)
        )
        cart_items = result.all()

        if not cart_items:
            return None

        total_sum = sum(product.price * cart.quantity for cart, product in cart_items)

        new_order = Order(
            user_id=user_id,
            shop_id=shop_id,
            total_price=total_sum,
            status="Yangi",
            payment_status="pending",
            phone=phone,
            delivery_address=address
        )
        session.add(new_order)
        await session.flush()

        for cart, product in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=cart.quantity,
                price=product.price
            )
            session.add(order_item)
            await session.delete(cart)

        await session.commit()
        return new_order.id


async def get_all_orders(shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.shop_id == shop_id).order_by(Order.id.desc())
        )
        return result.scalars().all()


async def update_order_status(order_id: int, status: str):
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        if order:
            order.status = status
            await session.commit()

async def update_product_price(product_id: int, new_price: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if product:
            product.price = new_price
            await session.commit()


async def update_product_quantity(product_id: int, new_quantity: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if product:
            product.quantity = new_quantity
            await session.commit()

from sqlalchemy import or_


async def search_products(shop_id: int, query: str):
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(
                Product.shop_id == shop_id,
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%")
                )
            )
        )
        return result.scalars().all()


async def get_user_orders(user_id: int, shop_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == user_id, Order.shop_id == shop_id).order_by(Order.id.desc())
        )
        return result.scalars().all()


async def update_cart_quantity(cart_id: int, new_quantity: int):
    async with async_session() as session:
        result = await session.execute(select(CartItem).where(CartItem.id == cart_id))
        item = result.scalars().first()
        if item:
            if new_quantity <= 0:
                await session.delete(item)
            else:
                item.quantity = new_quantity
            await session.commit()


async def get_cart_item_by_id(cart_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.id == cart_id)
        )
        return result.first()
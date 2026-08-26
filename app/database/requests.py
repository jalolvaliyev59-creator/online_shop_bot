from sqlalchemy import select
from app.database.connection import async_session
from app.models.product import Category, Product
from app.models.cart import Cart
from app.models.order import Order
from app.models.order_item import OrderItem

async def get_categories():
    async with async_session() as session:
        result = await session.execute(select(Category))
        return result.scalars().all()

async def add_initial_categories():
    async with async_session() as session:
        existing = await session.execute(select(Category))
        if existing.scalars().first():
            return
            
        categories = [
            Category(name="📱 Smartfonlar"),
            Category(name="🎧 Aksessuarlar"),
            Category(name="⌚ Gadjetlar")
        ]
        session.add_all(categories)
        await session.commit()

async def get_products_by_category(category_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.category_id == category_id)
        )
        return result.scalars().all()

async def get_product_by_id(product_id: int):
    """ID bo'yicha bitta mahsulotni topish"""
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalars().first()

async def add_initial_products():
    async with async_session() as session:
        existing = await session.execute(select(Product))
        if existing.scalars().first():
            return
            
        products = [
            Product(name="iPhone 13", price=8500000, category_id=1, description="Holati ideal, xotirasi 128GB"),
            Product(name="Samsung Galaxy S23", price=9000000, category_id=1, description="Yangi, qadoqda"),
            Product(name="AirPods Pro 2", price=2500000, category_id=2, description="Original simsiz quloqchin"),
            Product(name="Smart Watch 8", price=600000, category_id=3, description="Ajoyib aqlli soat")
        ]
        session.add_all(products)
        await session.commit()

async def add_to_cart(user_id: int, product_id: int):
    """Mahsulotni savatchaga qo'shish yoki miqdorini oshirish"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
        )
        cart_item = result.scalars().first()
        
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
            session.add(cart_item)
            
        await session.commit()

async def get_user_cart(user_id: int):
    """Foydalanuvchining savatchasidagi mahsulotlarni va ularning ma'lumotlarini olish"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart, Product)
            .join(Product, Cart.product_id == Product.id)
            .where(Cart.user_id == user_id)
        )
        return result.all()

async def clear_cart(user_id: int):
    """Foydalanuvchining savatchasini tozalash"""
    async with async_session() as session:
        result = await session.execute(select(Cart).where(Cart.user_id == user_id))
        items = result.scalars().all()
        for item in items:
            await session.delete(item)
        await session.commit()

async def create_order_from_cart(user_id: int, phone: str, address: str):
    """Savatchadagi mahsulotlardan buyurtma yaratish va savatchani bo'shatish"""
    async with async_session() as session:
        # 1. Savatchadagi mahsulotlarni olib kelamiz
        result = await session.execute(
            select(Cart, Product)
            .join(Product, Cart.product_id == Product.id)
            .where(Cart.user_id == user_id)
        )
        cart_items = result.all()
        
        if not cart_items:
            return None
            
        # 2. Umumiy summani hisoblaymiz
        total_sum = sum(product.price * cart.quantity for cart, product in cart_items)
        
        # 3. Yangi buyurtma yaratamiz (telefon va manzil bilan)
        new_order = Order(
            user_id=user_id, 
            total_price=total_sum, 
            status="Yangi",
            payment_status="pending",
            phone=phone,
            delivery_address=address
        )
        session.add(new_order)
        await session.flush() # ID olish uchun flush qilamiz
        
        # 4. Buyurtma elementlarini qo'shamiz va savatchani tozalaymiz
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

async def add_product(data: dict):
    """Admin tomonidan yangi mahsulot qo'shish"""
    async with async_session() as session:
        product = Product(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            category_id=int(data["category_id"])
        )
        session.add(product)
        await session.commit()

from app.models.order import Order


async def add_category(name: str):
    async with async_session() as session:
        session.add(Category(name=name))
        await session.commit()


async def get_all_products():
    async with async_session() as session:
        result = await session.execute(select(Product))
        return result.scalars().all()


async def delete_product(product_id: int):
    async with async_session() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if product:
            await session.delete(product)
            await session.commit()


async def get_all_orders():
    async with async_session() as session:
        result = await session.execute(select(Order).order_by(Order.id.desc()))
        return result.scalars().all()


async def update_order_status(order_id: int, status: str):
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        if order:
            order.status = status
            await session.commit()
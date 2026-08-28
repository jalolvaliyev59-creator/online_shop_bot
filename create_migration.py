import asyncio
from sqlalchemy import select
from app.database.connection import engine, Base, async_session
import app.models
from app.models.shop import Shop
from app.models.product import Category, Product


OLD_CATEGORIES = [
    (1, '📱 Smartfonlar'),
    (2, '🎧 Aksessuarlar'),
    (3, '⌚ Gadjetlar'),
    (4, '📋 Mahsulotlar'),
]

OLD_PRODUCTS = [
    (1, 'iPhone 13', 'Holati ideal, xotirasi 128GB', 8500000, 0, 1, None, 1),
    (2, 'Samsung Galaxy S23', 'Yangi, qadoqda', 9000000, 0, 1, None, 1),
    (3, 'AirPods Pro 2', 'Original simsiz quloqchin', 2500000, 0, 2, None, 1),
    (4, 'Smart Watch 8', 'Ajoyib aqlli soat', 600000, 0, 3, None, 1),
    (5, 'Hash', 'Shdhfhjs', 12000099, 0, 1, None, 1),
    (6, 'Jan', 'Kam', 122300, 0, 3, None, 1),
]


async def migrate():
    async with async_session() as session:
        result = await session.execute(select(Shop))
        shop = result.scalars().first()

        if shop:
            print(f"Do'kon allaqachon mavjud: ID {shop.id}")
        else:
            shop = Shop(name="Birinchi do'kon", owner_id=5228501591, start_code="shop1")
            session.add(shop)
            await session.flush()
            print(f"Yangi do'kon yaratildi: ID {shop.id}")

        cat_result = await session.execute(select(Category).where(Category.shop_id == shop.id))
        if cat_result.scalars().first():
            print("Kategoriyalar allaqachon mavjud, hech narsa qilinmaydi.")
            return

        old_to_new_cat = {}
        for old_id, name in OLD_CATEGORIES:
            cat = Category(name=name, shop_id=shop.id)
            session.add(cat)
            await session.flush()
            old_to_new_cat[old_id] = cat.id

        for old_id, name, description, price, quantity, category_id, image, is_active in OLD_PRODUCTS:
            new_cat_id = old_to_new_cat.get(category_id)
            if new_cat_id is None:
                continue
            product = Product(
                name=name,
                description=description,
                price=price,
                quantity=quantity,
                category_id=new_cat_id,
                shop_id=shop.id,
                image=image,
                is_active=bool(is_active)
            )
            session.add(product)

        await session.commit()
        print(f"Migratsiya tugadi! Do'kon ID: {shop.id}, start_code: {shop.start_code}")


if __name__ == "__main__":
    asyncio.run(migrate())

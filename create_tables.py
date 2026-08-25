import asyncio
from app.database.connection import engine, init_db
import app.models

async def main():
    await init_db()
    print("Barcha jadvallar yaratildi!")

asyncio.run(main())

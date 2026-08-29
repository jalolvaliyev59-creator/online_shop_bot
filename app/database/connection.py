import os
from sqlalchemy.ext.asyncio import create_async_engine

# Render muhitidan DATABASE_URL ni olish
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgresql://", "postgresql+asyncpg://", 1
  )

# Bulutli bazalar uchun SSL ulanishini majburiy qilish
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"ssl": "require"},
)
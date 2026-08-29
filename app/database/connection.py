
import os
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL Render Environment Variables'da topilmadi")

# Render DATABASE_URL:
# postgresql://...
# SQLAlchemy async uchun:
# postgresql+asyncpg://...
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1
    )

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "ssl": "require",
        "timeout": 30,
    },
)

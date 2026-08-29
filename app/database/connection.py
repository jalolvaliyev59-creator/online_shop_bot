import os
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL topilmadi")

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
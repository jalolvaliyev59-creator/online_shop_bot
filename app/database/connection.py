from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings
from app.models import Base

engine = create_async_engine(
    settings.DB_URL,  # <-- DATABASE_URL emas, aynan DB_URL bo'lishi kerak
    echo=True, 
    connect_args={"ssl": "require"} 
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
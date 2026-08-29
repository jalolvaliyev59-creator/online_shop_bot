from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database.base import Base
from config import settings

connect_args = {}
if "postgresql" in settings.DB_URL:
    connect_args = {"ssl": "require"}

engine = create_async_engine(
    settings.DB_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
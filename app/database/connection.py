from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings # yoki DB_URL qayerdan olinsa

# Asinxron dvigatelni yaratish
engine = create_async_engine(settings.DB_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    # Jadvallarni yaratish
    from app.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
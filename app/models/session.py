from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    current_shop_id: Mapped[int] = mapped_column(Integer, nullable=True)
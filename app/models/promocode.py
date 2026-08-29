from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Promocode(Base):
    __tablename__ = "promocodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
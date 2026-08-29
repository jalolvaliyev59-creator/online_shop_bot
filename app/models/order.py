from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from sqlalchemy import DateTime, ForeignKey, Integer, BigInteger, String, func



class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
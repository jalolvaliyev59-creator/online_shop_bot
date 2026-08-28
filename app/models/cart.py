from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class CartItem(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)

    product: Mapped["Product"] = relationship()
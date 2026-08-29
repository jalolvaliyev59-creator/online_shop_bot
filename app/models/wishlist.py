from sqlalchemy import ForeignKey, Integer, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class Wishlist(Base):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
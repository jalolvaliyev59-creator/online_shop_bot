from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class Feedback(Base):
    __tablename__ = "feedback"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
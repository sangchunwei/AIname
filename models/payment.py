from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class PaymentTransaction(Base):
    __tablename__ = "payment_transaction"
    __table_args__ = (
        UniqueConstraint("business_type", "business_order_id", name="uq_payment_business_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    out_trade_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="alipay_sandbox", index=True)
    business_type: Mapped[str] = mapped_column(String(30), index=True)
    business_order_id: Mapped[int] = mapped_column(Integer, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    alipay_trade_no: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    raw_notify: Mapped[str | None] = mapped_column(Text, nullable=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

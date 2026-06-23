from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ExpertProfile(Base):
    __tablename__ = "expert_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    accepting_orders: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ExpertService(Base):
    __tablename__ = "expert_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profile.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(Integer)
    delivery_days: Mapped[int] = mapped_column(Integer, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ExpertOrder(Base):
    __tablename__ = "expert_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("expert_service.id"), index=True)
    expert_id: Mapped[int] = mapped_column(ForeignKey("expert_profile.id"), index=True)
    selected_name: Mapped[str] = mapped_column(String(100))
    requirements: Mapped[str] = mapped_column(Text)
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending_payment", index=True)
    ai_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class VipPlan(Base):
    __tablename__ = "vip_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer)
    duration_days: Mapped[int] = mapped_column(Integer)
    daily_name_limit: Mapped[int] = mapped_column(Integer)
    daily_visual_limit: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("vip_plan.id"))
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class VipOrder(Base):
    __tablename__ = "vip_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("vip_plan.id"))
    amount_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    payment_provider: Mapped[str] = mapped_column(String(30), default="mock")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UsageCounter(Base):
    __tablename__ = "usage_counter"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", "action", name="uq_usage_user_date_action"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, default=date.today)
    action: Mapped[str] = mapped_column(String(50))
    used_count: Mapped[int] = mapped_column(Integer, default=0)

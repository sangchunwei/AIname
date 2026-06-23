from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class WalletAccount(Base):
    __tablename__ = "wallet_account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    available_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    frozen_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    pending_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_earned_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_withdrawn_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    bonus_ai_credits: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class WalletLedger(Base):
    __tablename__ = "wallet_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(50), index=True)
    available_delta: Mapped[int] = mapped_column(Integer, default=0)
    frozen_delta: Mapped[int] = mapped_column(Integer, default=0)
    pending_delta: Mapped[int] = mapped_column(Integer, default=0)
    bonus_delta: Mapped[int] = mapped_column(Integer, default=0)
    available_after: Mapped[int] = mapped_column(Integer)
    frozen_after: Mapped[int] = mapped_column(Integer)
    pending_after: Mapped[int] = mapped_column(Integer)
    bonus_after: Mapped[int] = mapped_column(Integer)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)


class RechargeOrder(Base):
    __tablename__ = "recharge_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(30), default="mock")
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(30))
    destination: Mapped[str] = mapped_column(String(300))
    account_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ReferralCode(Base):
    __tablename__ = "referral_code"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    qr_file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ReferralRelation(Base):
    __tablename__ = "referral_relation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    invitee_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    referral_code_id: Mapped[int] = mapped_column(ForeignKey("referral_code.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PartnerProfile(Base):
    __tablename__ = "partner_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, index=True)
    business_type: Mapped[str] = mapped_column(String(100))
    business_name: Mapped[str] = mapped_column(String(200))
    contact_info: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    commission_bps: Mapped[int] = mapped_column(Integer, default=1000)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CommissionRecord(Base):
    __tablename__ = "commission_record"
    __table_args__ = (
        UniqueConstraint("beneficiary_user_id", "source_type", "source_order_id", "commission_type", name="uq_commission_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    source_user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50))
    source_order_id: Mapped[int] = mapped_column(Integer)
    commission_type: Mapped[str] = mapped_column(String(30))
    gross_amount_cents: Mapped[int] = mapped_column(Integer)
    platform_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    commission_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

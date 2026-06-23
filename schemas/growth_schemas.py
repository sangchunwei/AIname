from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RechargeCreateIn(BaseModel):
    amount_cents: int = Field(..., ge=100, le=10000000)


class WithdrawalCreateIn(BaseModel):
    amount_cents: int = Field(..., ge=100, le=10000000)
    method: Literal["wechat", "alipay", "bank"]
    destination: str = Field(..., min_length=3, max_length=300)
    account_name: str = Field(..., min_length=2, max_length=100)


class PartnerApplyIn(BaseModel):
    business_type: str = Field(..., min_length=2, max_length=100)
    business_name: str = Field(..., min_length=2, max_length=200)
    contact_info: str = Field(..., min_length=3, max_length=200)


class ReviewIn(BaseModel):
    approved: bool
    note: str | None = Field(default=None, max_length=500)


class PartnerReviewIn(ReviewIn):
    commission_bps: int = Field(default=1000, ge=0, le=5000)


class WalletSummaryOut(BaseModel):
    available_cents: int
    frozen_cents: int
    pending_cents: int
    total_earned_cents: int
    total_withdrawn_cents: int
    bonus_ai_credits: int


class ReferralOut(BaseModel):
    code: str
    invite_url: str
    qr_file_url: str | None
    invited_count: int


class GrowthCenterOut(BaseModel):
    wallet: WalletSummaryOut
    referral: ReferralOut
    partner: dict | None
    ledger: list[dict]
    withdrawals: list[dict]
    commissions: list[dict]

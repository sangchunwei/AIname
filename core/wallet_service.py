from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from models.growth import (
    CommissionRecord, PartnerProfile, ReferralRelation, WalletAccount, WalletLedger,
)


async def get_wallet(session: AsyncSession, user_id: int, lock: bool = False) -> WalletAccount:
    stmt = select(WalletAccount).where(WalletAccount.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update()
    wallet = await session.scalar(stmt)
    if not wallet:
        wallet = WalletAccount(user_id=user_id)
        session.add(wallet)
        await session.flush()
    return wallet


async def post_wallet_entry(
    session: AsyncSession,
    *, user_id: int, entry_type: str, description: str, idempotency_key: str,
    available_delta: int = 0, frozen_delta: int = 0, pending_delta: int = 0, bonus_delta: int = 0,
    reference_type: str | None = None, reference_id: int | None = None,
    earned_delta: int = 0, withdrawn_delta: int = 0,
) -> WalletLedger:
    existing = await session.scalar(select(WalletLedger).where(WalletLedger.idempotency_key == idempotency_key))
    if existing:
        return existing
    wallet = await get_wallet(session, user_id, lock=True)
    available = wallet.available_cents + available_delta
    frozen = wallet.frozen_cents + frozen_delta
    pending = wallet.pending_cents + pending_delta
    bonus = wallet.bonus_ai_credits + bonus_delta
    if min(available, frozen, pending, bonus) < 0:
        raise HTTPException(status_code=400, detail="账户余额不足")
    wallet.available_cents, wallet.frozen_cents, wallet.pending_cents = available, frozen, pending
    wallet.bonus_ai_credits = bonus
    wallet.total_earned_cents += earned_delta
    wallet.total_withdrawn_cents += withdrawn_delta
    entry = WalletLedger(
        user_id=user_id, entry_type=entry_type,
        available_delta=available_delta, frozen_delta=frozen_delta, pending_delta=pending_delta, bonus_delta=bonus_delta,
        available_after=available, frozen_after=frozen, pending_after=pending, bonus_after=bonus,
        reference_type=reference_type, reference_id=reference_id,
        idempotency_key=idempotency_key, description=description,
    )
    session.add(entry)
    await session.flush()
    return entry


async def create_partner_commission(
    session: AsyncSession, *, buyer_user_id: int, source_type: str, source_order_id: int, gross_cents: int,
) -> CommissionRecord | None:
    relation = await session.scalar(select(ReferralRelation).where(ReferralRelation.invitee_user_id == buyer_user_id))
    if not relation:
        return None
    partner = await session.scalar(
        select(PartnerProfile).where(PartnerProfile.user_id == relation.inviter_user_id, PartnerProfile.status == "approved")
    )
    if not partner:
        return None
    existing = await session.scalar(select(CommissionRecord).where(
        CommissionRecord.beneficiary_user_id == partner.user_id,
        CommissionRecord.source_type == source_type,
        CommissionRecord.source_order_id == source_order_id,
        CommissionRecord.commission_type == "partner",
    ))
    if existing:
        return existing
    amount = gross_cents * partner.commission_bps // 10000
    if amount <= 0:
        return None
    record = CommissionRecord(
        beneficiary_user_id=partner.user_id, source_user_id=buyer_user_id,
        source_type=source_type, source_order_id=source_order_id,
        commission_type="partner", gross_amount_cents=gross_cents,
        platform_fee_cents=0, commission_cents=amount, status="pending",
    )
    session.add(record)
    await session.flush()
    await post_wallet_entry(
        session, user_id=partner.user_id, entry_type="partner_commission_pending",
        pending_delta=amount, reference_type="commission", reference_id=record.id,
        idempotency_key=f"partner-pending:{record.id}", description="合伙人订单佣金进入待结算余额",
    )
    return record


async def settle_commission(session: AsyncSession, record: CommissionRecord) -> None:
    if record.status == "settled":
        return
    await post_wallet_entry(
        session, user_id=record.beneficiary_user_id, entry_type=f"{record.commission_type}_commission_settled",
        available_delta=record.commission_cents, pending_delta=-record.commission_cents,
        earned_delta=record.commission_cents, reference_type="commission", reference_id=record.id,
        idempotency_key=f"commission-settle:{record.id}", description="佣金结算至可用余额",
    )
    record.status = "settled"
    record.settled_at = datetime.now()


async def credit_expert_income(
    session: AsyncSession, *, expert_user_id: int, customer_user_id: int,
    order_id: int, gross_cents: int,
) -> CommissionRecord:
    existing = await session.scalar(select(CommissionRecord).where(
        CommissionRecord.beneficiary_user_id == expert_user_id,
        CommissionRecord.source_type == "expert_order",
        CommissionRecord.source_order_id == order_id,
        CommissionRecord.commission_type == "expert",
    ))
    if existing:
        return existing
    fee = gross_cents * settings.EXPERT_PLATFORM_FEE_BPS // 10000
    net = gross_cents - fee
    record = CommissionRecord(
        beneficiary_user_id=expert_user_id, source_user_id=customer_user_id,
        source_type="expert_order", source_order_id=order_id,
        commission_type="expert", gross_amount_cents=gross_cents,
        platform_fee_cents=fee, commission_cents=net, status="settled", settled_at=datetime.now(),
    )
    session.add(record)
    await session.flush()
    await post_wallet_entry(
        session, user_id=expert_user_id, entry_type="expert_service_income",
        available_delta=net, earned_delta=net, reference_type="expert_order", reference_id=order_id,
        idempotency_key=f"expert-income:{order_id}",
        description=f"专家服务收入，平台服务费 {fee / 100:.2f} 元",
    )
    return record

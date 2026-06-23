from pathlib import Path
from uuid import uuid4

import qrcode
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from core.wallet_service import get_wallet, post_wallet_entry
from models.growth import ReferralCode, ReferralRelation


async def get_or_create_referral(session: AsyncSession, user_id: int) -> ReferralCode:
    referral = await session.scalar(select(ReferralCode).where(ReferralCode.user_id == user_id))
    if referral:
        return referral
    code = uuid4().hex[:10].upper()
    referral = ReferralCode(user_id=user_id, code=code)
    session.add(referral)
    await session.flush()
    invite_url = f"{settings.PUBLIC_H5_URL}/#/pages/register/register?invite={code}"
    relative = f"referrals/{code}.png"
    path = Path(settings.GENERATED_ASSET_DIR) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    qrcode.make(invite_url).save(path)
    referral.qr_file_url = f"{settings.PUBLIC_ASSET_PREFIX}/{relative}"
    await session.flush()
    return referral


async def bind_referral(session: AsyncSession, invitee_user_id: int, invite_code: str | None) -> None:
    if not invite_code:
        return
    code = await session.scalar(select(ReferralCode).where(ReferralCode.code == invite_code.strip().upper()))
    if not code or code.user_id == invitee_user_id:
        return
    existing = await session.scalar(select(ReferralRelation).where(ReferralRelation.invitee_user_id == invitee_user_id))
    if existing:
        return
    session.add(ReferralRelation(
        inviter_user_id=code.user_id, invitee_user_id=invitee_user_id, referral_code_id=code.id,
    ))
    await post_wallet_entry(
        session, user_id=code.user_id, entry_type="invite_reward", bonus_delta=settings.INVITER_REWARD_CREDITS,
        reference_type="invited_user", reference_id=invitee_user_id,
        idempotency_key=f"invite-reward:inviter:{invitee_user_id}", description="邀请好友注册奖励 AI 推演次数",
    )
    await post_wallet_entry(
        session, user_id=invitee_user_id, entry_type="invitee_reward", bonus_delta=settings.INVITEE_REWARD_CREDITS,
        reference_type="referrer", reference_id=code.user_id,
        idempotency_key=f"invite-reward:invitee:{invitee_user_id}", description="通过邀请注册获得 AI 推演次数",
    )


async def referral_summary(session: AsyncSession, user_id: int):
    referral = await get_or_create_referral(session, user_id)
    count = await session.scalar(select(func.count(ReferralRelation.id)).where(ReferralRelation.inviter_user_id == user_id))
    return {
        "code": referral.code,
        "invite_url": f"{settings.PUBLIC_H5_URL}/#/pages/register/register?invite={referral.code}",
        "qr_file_url": referral.qr_file_url,
        "invited_count": count or 0,
    }

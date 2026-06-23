from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from models.membership import UsageCounter, UserSubscription, VipPlan
from models.growth import WalletAccount
from core.wallet_service import post_wallet_entry


async def get_active_membership(session: AsyncSession, user_id: int):
    now = datetime.now()
    row = (
        await session.execute(
            select(UserSubscription, VipPlan)
            .join(VipPlan, VipPlan.id == UserSubscription.plan_id)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active",
                UserSubscription.expires_at > now,
            )
            .order_by(UserSubscription.expires_at.desc())
            .limit(1)
        )
    ).first()
    return row


async def get_limits(session: AsyncSession, user_id: int) -> tuple[int, int, object | None]:
    membership = await get_active_membership(session, user_id)
    if membership:
        subscription, plan = membership
        return plan.daily_name_limit, plan.daily_visual_limit, (subscription, plan)
    return settings.FREE_DAILY_NAME_LIMIT, settings.FREE_DAILY_VISUAL_LIMIT, None


async def get_used(session: AsyncSession, user_id: int, action: str) -> int:
    counter = await session.scalar(
        select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.usage_date == date.today(),
            UsageCounter.action == action,
        )
    )
    return counter.used_count if counter else 0


async def ensure_quota(session: AsyncSession, user_id: int, action: str) -> None:
    name_limit, visual_limit, _ = await get_limits(session, user_id)
    limit = name_limit if action == "name_generation" else visual_limit
    used = await get_used(session, user_id, action)
    if used >= limit:
        if action == "name_generation":
            wallet = await session.scalar(select(WalletAccount).where(WalletAccount.user_id == user_id))
            if wallet and wallet.bonus_ai_credits > 0:
                return
        raise HTTPException(status_code=429, detail="今日额度已用完，升级 VIP 或邀请好友可获得更多额度")


async def consume_quota(session: AsyncSession, user_id: int, action: str) -> None:
    name_limit, visual_limit, _ = await get_limits(session, user_id)
    limit = name_limit if action == "name_generation" else visual_limit
    counter = await session.scalar(
        select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.usage_date == date.today(),
            UsageCounter.action == action,
        )
    )
    if action == "name_generation" and counter and counter.used_count >= limit:
        await post_wallet_entry(
            session, user_id=user_id, entry_type="bonus_ai_credit_used", bonus_delta=-1,
            idempotency_key=f"bonus-use:{user_id}:{datetime.now().timestamp()}", description="使用邀请奖励 AI 推演次数",
        )
    elif counter:
        counter.used_count += 1
    else:
        session.add(UsageCounter(user_id=user_id, usage_date=date.today(), action=action, used_count=1))
    await session.commit()


async def activate_subscription(session: AsyncSession, user_id: int, plan: VipPlan) -> UserSubscription:
    current = await get_active_membership(session, user_id)
    now = datetime.now()
    starts_at = current[0].expires_at if current else now
    subscription = UserSubscription(
        user_id=user_id,
        plan_id=plan.id,
        status="active",
        starts_at=now,
        expires_at=starts_at + timedelta(days=plan.duration_days),
    )
    session.add(subscription)
    await session.flush()
    return subscription

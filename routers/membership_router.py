from datetime import datetime
from uuid import uuid4

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from core.auth import AuthHandler
from core.membership_service import activate_subscription, get_active_membership, get_limits, get_used
from core.wallet_service import create_partner_commission
from core.avatar_service import (
    ALLOWED_CONTENT_TYPES, DEFAULT_AVATARS, MAX_AVATAR_BYTES, AvatarValidationError,
    delete_local_avatar, get_default_avatar, save_avatar,
)
from dependencies import get_session
from models.membership import UserProfile, VipOrder, VipPlan
from models.user import User
from routers.admin_router import require_admin
from schemas.membership_schemas import (
    DefaultAvatarSelectIn, PasswordChangeIn, ProfileUpdateIn, UserCenterOut, VipGrantIn, VipOrderCreateIn,
    VipOrderOut, VipPlanOut,
)


router = APIRouter(tags=["用户中心与VIP"])
auth_handler = AuthHandler()


@router.get("/me", response_model=UserCenterOut)
async def get_user_center(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.id == user_id))
    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    name_limit, visual_limit, membership = await get_limits(session, user_id)
    return {
        "id": user.id, "email": user.email, "username": user.username,
        "avatar_url": profile.avatar_url if profile else None,
        "bio": profile.bio if profile else None,
        "created_at": user.created_at, "is_expert": user.is_expert,
        "subscription": {
            "is_vip": bool(membership),
            "plan_name": membership[1].name if membership else None,
            "expires_at": membership[0].expires_at if membership else None,
        },
        "usage": {
            "name_used": await get_used(session, user_id, "name_generation"),
            "name_limit": name_limit,
            "visual_used": await get_used(session, user_id, "visual_generation"),
            "visual_limit": visual_limit,
        },
    }


@router.patch("/me/profile")
async def update_profile(
    data: ProfileUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.id == user_id))
    user.username = data.username
    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id)
        session.add(profile)
    profile.bio = data.bio
    await session.commit()
    return {"message": "个人资料已更新"}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        await file.close()
        raise HTTPException(status_code=400, detail="仅支持 JPEG、PNG 和 WebP 图片")

    content = await file.read(MAX_AVATAR_BYTES + 1)
    await file.close()
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="头像文件不能超过 5 MB")

    try:
        avatar_url, _ = await asyncio.to_thread(save_avatar, content, user_id)
    except AvatarValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id)
        session.add(profile)
    old_avatar_url = profile.avatar_url
    profile.avatar_url = avatar_url
    try:
        await session.commit()
    except Exception:
        await asyncio.to_thread(delete_local_avatar, avatar_url)
        raise

    await asyncio.to_thread(delete_local_avatar, old_avatar_url)
    return {"avatar_url": avatar_url}


@router.get("/me/avatar/defaults")
async def list_default_avatars(
    _: int = Depends(auth_handler.auth_access_dependency),
):
    return DEFAULT_AVATARS


@router.put("/me/avatar/default")
async def select_default_avatar(
    data: DefaultAvatarSelectIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    selected = get_default_avatar(data.avatar_key)
    if not selected:
        raise HTTPException(status_code=400, detail="默认头像不存在")

    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        profile = UserProfile(user_id=user_id)
        session.add(profile)
    old_avatar_url = profile.avatar_url
    profile.avatar_url = selected["url"]
    await session.commit()
    await asyncio.to_thread(delete_local_avatar, old_avatar_url)
    return {"avatar_url": selected["url"]}


@router.delete("/me/avatar")
async def reset_avatar(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    profile = await session.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile or not profile.avatar_url:
        return {"message": "已恢复默认头像", "avatar_url": None}

    old_avatar_url = profile.avatar_url
    profile.avatar_url = None
    await session.commit()
    await asyncio.to_thread(delete_local_avatar, old_avatar_url)
    return {"message": "已恢复默认头像", "avatar_url": None}


@router.post("/me/password")
async def change_password(
    data: PasswordChangeIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.id == user_id))
    if not user.check_password(data.current_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    user.password = data.new_password
    user.token_version += 1
    await session.commit()
    return {"message": "密码修改成功，请重新登录"}


@router.get("/vip/plans", response_model=list[VipPlanOut])
async def list_vip_plans(session: AsyncSession = Depends(get_session)):
    return list((await session.scalars(select(VipPlan).where(VipPlan.is_active.is_(True)).order_by(VipPlan.price_cents))).all())


@router.post("/vip/orders", response_model=VipOrderOut)
async def create_vip_order(
    data: VipOrderCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    plan = await session.scalar(select(VipPlan).where(VipPlan.code == data.plan_code, VipPlan.is_active.is_(True)))
    if not plan:
        raise HTTPException(status_code=404, detail="VIP 套餐不存在")
    order = VipOrder(
        order_no=f"VIP{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}",
        user_id=user_id, plan_id=plan.id, amount_cents=plan.price_cents,
        status="pending", payment_provider="pending",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


@router.post("/vip/orders/{order_id}/mock-pay", response_model=VipOrderOut)
async def mock_pay_vip_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    raise HTTPException(status_code=410, detail="本地模拟支付已停用，请使用支付宝沙箱支付或余额支付")
    if not settings.MOCK_PAYMENT_ENABLED:
        raise HTTPException(status_code=403, detail="模拟支付未启用")
    order = await session.scalar(select(VipOrder).where(VipOrder.id == order_id, VipOrder.user_id == user_id))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "paid":
        plan = await session.scalar(select(VipPlan).where(VipPlan.id == order.plan_id))
        await activate_subscription(session, user_id, plan)
        order.status = "paid"
        order.paid_at = datetime.now()
        await create_partner_commission(session, buyer_user_id=user_id, source_type="vip_order", source_order_id=order.id, gross_cents=order.amount_cents)
        await session.commit()
        await session.refresh(order)
    return order


@router.get("/vip/orders", response_model=list[VipOrderOut])
async def list_vip_orders(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return list((await session.scalars(select(VipOrder).where(VipOrder.user_id == user_id).order_by(VipOrder.id.desc()))).all())


@router.post("/vip/admin/grant")
async def admin_grant_vip(
    data: VipGrantIn,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.id == data.user_id, User.is_deleted.is_(False)))
    plan = await session.scalar(select(VipPlan).where(VipPlan.code == data.plan_code, VipPlan.is_active.is_(True)))
    if not user or not plan:
        raise HTTPException(status_code=404, detail="用户或套餐不存在")
    subscription = await activate_subscription(session, user.id, plan)
    await session.commit()
    return {"message": "VIP 已开通", "expires_at": subscription.expires_at}

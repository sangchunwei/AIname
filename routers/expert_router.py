from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from core.auth import AuthHandler
from core.expert_service import generate_expert_ai_draft
from core.membership_service import get_active_membership
from core.wallet_service import create_partner_commission, credit_expert_income
from dependencies import get_session
from models.expert import ExpertOrder, ExpertProfile, ExpertService
from models.user import User
from routers.admin_router import require_admin
from schemas.expert_schemas import (
    ExpertOrderCreateIn, ExpertOrderOut, ExpertReportIn, ExpertServiceCreateIn,
    ExpertServiceOut, ExpertVerifyIn,
)


router = APIRouter(prefix="/experts", tags=["专家精批"])
auth_handler = AuthHandler()
PAYMENT_TIMEOUT_MINUTES = 10


async def require_expert(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
) -> ExpertProfile:
    profile = await session.scalar(
        select(ExpertProfile).where(ExpertProfile.user_id == user_id, ExpertProfile.is_verified.is_(True))
    )
    if not profile:
        raise HTTPException(status_code=403, detail="当前账号不是已认证专家")
    return profile


def service_output(service: ExpertService, expert: ExpertProfile):
    return {
        "id": service.id, "expert_id": expert.id, "expert_name": expert.display_name,
        "expert_title": expert.title, "category": expert.category,
        "name": service.name, "description": service.description,
        "price_cents": service.price_cents, "delivery_days": service.delivery_days,
    }


def order_output(order: ExpertOrder, customer: User | None = None):
    return {
        "id": order.id, "order_no": order.order_no, "user_id": order.user_id,
        "customer_username": customer.username if customer else None,
        "customer_email": customer.email if customer else None,
        "service_id": order.service_id, "expert_id": order.expert_id,
        "selected_name": order.selected_name, "requirements": order.requirements,
        "amount_cents": order.amount_cents, "status": order.status,
        "ai_draft": order.ai_draft, "final_report": order.final_report,
        "paid_at": order.paid_at, "delivered_at": order.delivered_at,
        "created_at": order.created_at,
    }


def expire_pending_order(order: ExpertOrder) -> bool:
    if order.status != "pending_payment":
        return False
    if order.created_at and order.created_at <= datetime.now() - timedelta(minutes=PAYMENT_TIMEOUT_MINUTES):
        order.status = "payment_timeout"
        return True
    return False


@router.get("/services", response_model=list[ExpertServiceOut])
async def list_expert_services(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(ExpertService, ExpertProfile)
            .join(ExpertProfile, ExpertProfile.id == ExpertService.expert_id)
            .where(
                ExpertService.is_active.is_(True), ExpertProfile.is_verified.is_(True),
                ExpertProfile.accepting_orders.is_(True),
            )
            .order_by(ExpertService.id.desc())
        )
    ).all()
    return [service_output(service, expert) for service, expert in rows]


@router.post("/orders", response_model=ExpertOrderOut)
async def create_expert_order(
    data: ExpertOrderCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    row = (
        await session.execute(
            select(ExpertService, ExpertProfile)
            .join(ExpertProfile, ExpertProfile.id == ExpertService.expert_id)
            .where(ExpertService.id == data.service_id, ExpertService.is_active.is_(True), ExpertProfile.is_verified.is_(True))
        )
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="专家服务不存在")
    service, expert = row
    is_vip = bool(await get_active_membership(session, user_id))
    amount = round(service.price_cents * 0.9) if is_vip else service.price_cents
    order = ExpertOrder(
        order_no=f"EXP{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}",
        user_id=user_id, service_id=service.id, expert_id=expert.id,
        selected_name=data.selected_name, requirements=data.requirements,
        amount_cents=amount, status="pending_payment",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


@router.post("/orders/{order_id}/mock-pay", response_model=ExpertOrderOut)
async def mock_pay_expert_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    if not settings.MOCK_PAYMENT_ENABLED:
        raise HTTPException(status_code=403, detail="模拟支付未启用")
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == user_id))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if expire_pending_order(order):
        await session.commit()
        raise HTTPException(status_code=400, detail="订单支付超时，已自动取消")
    if order.status == "pending_payment":
        order.status = "paid"
        order.paid_at = datetime.now()
        await create_partner_commission(session, buyer_user_id=user_id, source_type="expert_order", source_order_id=order.id, gross_cents=order.amount_cents)
        await session.commit()
        await session.refresh(order)
    return order


@router.get("/orders", response_model=list[ExpertOrderOut])
async def list_my_expert_orders(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    orders = list((await session.scalars(select(ExpertOrder).where(ExpertOrder.user_id == user_id).order_by(ExpertOrder.id.desc()))).all())
    expired = False
    for order in orders:
        expired = expire_pending_order(order) or expired
    if expired:
        await session.commit()
    return orders


@router.post("/orders/{order_id}/cancel", response_model=ExpertOrderOut)
async def cancel_expert_order(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == user_id))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if expire_pending_order(order):
        await session.commit()
        await session.refresh(order)
        return order
    if order.status != "pending_payment":
        raise HTTPException(status_code=400, detail="当前订单状态不允许取消")
    order.status = "canceled"
    await session.commit()
    await session.refresh(order)
    return order


@router.get("/workbench/orders", response_model=list[ExpertOrderOut])
async def list_expert_workbench_orders(
    expert: ExpertProfile = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
):
    rows = (
        await session.execute(
            select(ExpertOrder, User)
            .join(User, User.id == ExpertOrder.user_id)
            .where(ExpertOrder.expert_id == expert.id, ExpertOrder.status != "pending_payment")
            .order_by(ExpertOrder.id.desc())
        )
    ).all()
    return [order_output(order, customer) for order, customer in rows]


@router.post("/workbench/orders/{order_id}/ai-draft", response_model=ExpertOrderOut)
async def create_ai_draft(
    order_id: int,
    expert: ExpertProfile = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.expert_id == expert.id))
    if not order or order.status not in {"paid", "accepted", "drafting"}:
        raise HTTPException(status_code=400, detail="订单状态不允许生成初稿")
    order.ai_draft = await generate_expert_ai_draft(order, expert)
    order.status = "drafting"
    await session.commit()
    await session.refresh(order)
    return order


@router.post("/workbench/orders/{order_id}/report", response_model=ExpertOrderOut)
async def deliver_expert_report(
    order_id: int,
    data: ExpertReportIn,
    expert: ExpertProfile = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.expert_id == expert.id))
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "pending_payment" or not order.paid_at:
        raise HTTPException(status_code=400, detail="订单状态不允许交付")
    if order.status == "delivered":
        return order
    await credit_expert_income(
        session, expert_user_id=expert.user_id, customer_user_id=order.user_id,
        order_id=order.id, gross_cents=order.amount_cents,
    )
    order.final_report = data.final_report
    order.status = "delivered"
    order.delivered_at = datetime.now()
    await session.commit()
    await session.refresh(order)
    return order


@router.post("/admin/verify")
async def verify_expert(
    data: ExpertVerifyIn,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.scalar(select(User).where(User.id == data.user_id, User.is_deleted.is_(False)))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    profile = await session.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user.id))
    if not profile:
        profile = ExpertProfile(user_id=user.id)
        session.add(profile)
    for key, value in data.model_dump(exclude={"user_id"}).items():
        setattr(profile, key, value)
    profile.is_verified = True
    user.is_expert = True
    await session.commit()
    return {"message": "专家认证成功"}


@router.post("/workbench/services", response_model=ExpertServiceOut)
async def create_expert_service(
    data: ExpertServiceCreateIn,
    expert: ExpertProfile = Depends(require_expert),
    session: AsyncSession = Depends(get_session),
):
    service = ExpertService(expert_id=expert.id, **data.model_dump())
    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service_output(service, expert)

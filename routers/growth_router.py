from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from core.auth import AuthHandler
from core.growth_service import referral_summary
from core.membership_service import activate_subscription
from core.wallet_service import (
    create_partner_commission, get_wallet, post_wallet_entry, settle_commission,
)
from dependencies import get_session
from models.expert import ExpertOrder
from models.growth import (
    CommissionRecord, PartnerProfile, RechargeOrder, ReferralRelation,
    WalletLedger, WithdrawalRequest,
)
from models.membership import VipOrder, VipPlan
from models.user import User
from routers.admin_router import require_admin
from schemas.growth_schemas import (
    GrowthCenterOut, PartnerApplyIn, PartnerReviewIn, RechargeCreateIn,
    ReviewIn, WithdrawalCreateIn,
)


router = APIRouter(prefix="/growth", tags=["增长、钱包与分销"])
auth_handler = AuthHandler()
EXPERT_PAYMENT_TIMEOUT_MINUTES = 10


def dt(value):
    return value.isoformat() if value else None


@router.get("", response_model=GrowthCenterOut)
async def growth_center(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    wallet = await get_wallet(session, user_id)
    referral = await referral_summary(session, user_id)
    partner = await session.scalar(select(PartnerProfile).where(PartnerProfile.user_id == user_id))
    ledger = list((await session.scalars(select(WalletLedger).where(WalletLedger.user_id == user_id).order_by(WalletLedger.id.desc()).limit(50))).all())
    withdrawals = list((await session.scalars(select(WithdrawalRequest).where(WithdrawalRequest.user_id == user_id).order_by(WithdrawalRequest.id.desc()).limit(20))).all())
    commissions = list((await session.scalars(select(CommissionRecord).where(CommissionRecord.beneficiary_user_id == user_id).order_by(CommissionRecord.id.desc()).limit(50))).all())
    await session.commit()
    return {
        "wallet": {key: getattr(wallet, key) for key in ["available_cents", "frozen_cents", "pending_cents", "total_earned_cents", "total_withdrawn_cents", "bonus_ai_credits"]},
        "referral": referral,
        "partner": None if not partner else {"id": partner.id, "business_type": partner.business_type, "business_name": partner.business_name, "status": partner.status, "commission_bps": partner.commission_bps, "review_note": partner.review_note},
        "ledger": [{
            "id": x.id, "entry_type": x.entry_type,
            "available_delta": x.available_delta, "frozen_delta": x.frozen_delta,
            "pending_delta": x.pending_delta, "bonus_delta": x.bonus_delta,
            "description": x.description, "created_at": dt(x.created_at),
        } for x in ledger],
        "withdrawals": [{"id": x.id, "request_no": x.request_no, "amount_cents": x.amount_cents, "method": x.method, "status": x.status, "review_note": x.review_note, "created_at": dt(x.created_at)} for x in withdrawals],
        "commissions": [{"id": x.id, "commission_type": x.commission_type, "gross_amount_cents": x.gross_amount_cents, "platform_fee_cents": x.platform_fee_cents, "commission_cents": x.commission_cents, "status": x.status, "created_at": dt(x.created_at)} for x in commissions],
    }


@router.post("/recharges")
async def create_recharge(
    data: RechargeCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    order = RechargeOrder(
        order_no=f"RCG{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}",
        user_id=user_id,
        amount_cents=data.amount_cents,
        provider="alipay_sandbox",
    )
    session.add(order)
    await session.commit(); await session.refresh(order)
    return {"id": order.id, "order_no": order.order_no, "amount_cents": order.amount_cents, "status": order.status}


@router.post("/recharges/{order_id}/mock-pay")
async def mock_pay_recharge(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    raise HTTPException(status_code=410, detail="本地模拟充值已停用，请使用支付宝沙箱充值")
    if not settings.MOCK_PAYMENT_ENABLED:
        raise HTTPException(status_code=403, detail="模拟支付未启用")
    order = await session.scalar(select(RechargeOrder).where(RechargeOrder.id == order_id, RechargeOrder.user_id == user_id))
    if not order: raise HTTPException(status_code=404, detail="充值订单不存在")
    if order.status != "paid":
        await post_wallet_entry(session, user_id=user_id, entry_type="mock_recharge", available_delta=order.amount_cents,
            reference_type="recharge", reference_id=order.id, idempotency_key=f"recharge:{order.id}", description="本地模拟充值")
        order.status, order.paid_at = "paid", datetime.now()
        await session.commit()
    return {"message": "模拟充值成功"}


@router.post("/withdrawals")
async def create_withdrawal(
    data: WithdrawalCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    request = WithdrawalRequest(request_no=f"WDR{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:8].upper()}", user_id=user_id, **data.model_dump())
    session.add(request); await session.flush()
    await post_wallet_entry(session, user_id=user_id, entry_type="withdrawal_frozen",
        available_delta=-data.amount_cents, frozen_delta=data.amount_cents,
        reference_type="withdrawal", reference_id=request.id, idempotency_key=f"withdraw-freeze:{request.id}", description="提现申请冻结余额")
    await session.commit()
    return {"message": "提现申请已提交", "request_no": request.request_no}


@router.post("/partner/apply")
async def apply_partner(
    data: PartnerApplyIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    profile = await session.scalar(select(PartnerProfile).where(PartnerProfile.user_id == user_id))
    if profile and profile.status in {"pending", "approved"}:
        raise HTTPException(status_code=400, detail="已有待审核或已通过的合伙人申请")
    if not profile:
        profile = PartnerProfile(user_id=user_id, **data.model_dump(), commission_bps=settings.DEFAULT_PARTNER_COMMISSION_BPS)
        session.add(profile)
    else:
        for key, value in data.model_dump().items(): setattr(profile, key, value)
        profile.status, profile.review_note = "pending", None
    await session.commit()
    return {"message": "合伙人申请已提交"}


@router.post("/pay/vip/{order_id}")
async def pay_vip_with_balance(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(VipOrder).where(VipOrder.id == order_id, VipOrder.user_id == user_id))
    if not order: raise HTTPException(status_code=404, detail="VIP 订单不存在")
    if order.status != "paid":
        plan = await session.scalar(select(VipPlan).where(VipPlan.id == order.plan_id))
        await post_wallet_entry(session, user_id=user_id, entry_type="vip_purchase", available_delta=-order.amount_cents,
            reference_type="vip_order", reference_id=order.id, idempotency_key=f"wallet-vip:{order.id}", description=f"余额购买 {plan.name}")
        await activate_subscription(session, user_id, plan)
        order.status, order.payment_provider, order.paid_at = "paid", "wallet", datetime.now()
        await create_partner_commission(session, buyer_user_id=user_id, source_type="vip_order", source_order_id=order.id, gross_cents=order.amount_cents)
        await session.commit()
    return {"message": "VIP 余额支付成功"}


@router.post("/pay/expert/{order_id}")
async def pay_expert_with_balance(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == user_id))
    if not order: raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status == "pending_payment" and order.created_at and order.created_at <= datetime.now() - timedelta(minutes=EXPERT_PAYMENT_TIMEOUT_MINUTES):
        order.status = "payment_timeout"
        await session.commit()
        raise HTTPException(status_code=400, detail="订单支付超时，已自动取消")
    if order.status in {"payment_timeout", "canceled"}:
        raise HTTPException(status_code=400, detail="当前订单已取消，不能继续付款")
    if order.status != "pending_payment":
        return {"message": "专家订单已支付"}
    if order.status == "pending_payment":
        await post_wallet_entry(session, user_id=user_id, entry_type="expert_service_purchase", available_delta=-order.amount_cents,
            reference_type="expert_order", reference_id=order.id, idempotency_key=f"wallet-expert:{order.id}", description="余额购买专家精批服务")
        order.status, order.paid_at = "paid", datetime.now()
        await create_partner_commission(session, buyer_user_id=user_id, source_type="expert_order", source_order_id=order.id, gross_cents=order.amount_cents)
        await session.commit()
    return {"message": "专家服务余额支付成功"}


@router.get("/admin/review")
async def admin_review_center(
    _: User = Depends(require_admin), session: AsyncSession = Depends(get_session),
):
    withdrawals = list((await session.scalars(select(WithdrawalRequest).where(WithdrawalRequest.status == "pending").order_by(WithdrawalRequest.id))).all())
    partners = list((await session.scalars(select(PartnerProfile).where(PartnerProfile.status == "pending").order_by(PartnerProfile.id))).all())
    commissions = list((await session.scalars(select(CommissionRecord).where(CommissionRecord.status == "pending").order_by(CommissionRecord.id))).all())
    return {
        "withdrawals": [{"id": x.id, "user_id": x.user_id, "amount_cents": x.amount_cents, "method": x.method, "destination": x.destination, "account_name": x.account_name} for x in withdrawals],
        "partners": [{"id": x.id, "user_id": x.user_id, "business_type": x.business_type, "business_name": x.business_name, "contact_info": x.contact_info} for x in partners],
        "commissions": [{"id": x.id, "beneficiary_user_id": x.beneficiary_user_id, "commission_type": x.commission_type, "commission_cents": x.commission_cents} for x in commissions],
    }


@router.post("/admin/withdrawals/{request_id}/review")
async def review_withdrawal(request_id: int, data: ReviewIn, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    request = await session.scalar(select(WithdrawalRequest).where(WithdrawalRequest.id == request_id, WithdrawalRequest.status == "pending"))
    if not request: raise HTTPException(status_code=404, detail="待审核提现不存在")
    if data.approved:
        await post_wallet_entry(session, user_id=request.user_id, entry_type="mock_withdrawal_paid", frozen_delta=-request.amount_cents,
            withdrawn_delta=request.amount_cents, reference_type="withdrawal", reference_id=request.id,
            idempotency_key=f"withdraw-paid:{request.id}", description=f"模拟提现至 {request.method}")
        request.status = "paid"
    else:
        await post_wallet_entry(session, user_id=request.user_id, entry_type="withdrawal_rejected", available_delta=request.amount_cents, frozen_delta=-request.amount_cents,
            reference_type="withdrawal", reference_id=request.id, idempotency_key=f"withdraw-reject:{request.id}", description="提现驳回，余额退回")
        request.status = "rejected"
    request.review_note, request.reviewed_at = data.note, datetime.now(); await session.commit()
    return {"message": "提现审核完成"}


@router.post("/admin/partners/{partner_id}/review")
async def review_partner(partner_id: int, data: PartnerReviewIn, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    partner = await session.scalar(select(PartnerProfile).where(PartnerProfile.id == partner_id, PartnerProfile.status == "pending"))
    if not partner: raise HTTPException(status_code=404, detail="待审核合伙人不存在")
    partner.status = "approved" if data.approved else "rejected"
    partner.commission_bps, partner.review_note = data.commission_bps, data.note
    await session.commit(); return {"message": "合伙人审核完成"}


@router.post("/admin/commissions/{commission_id}/settle")
async def admin_settle_commission(commission_id: int, _: User = Depends(require_admin), session: AsyncSession = Depends(get_session)):
    record = await session.scalar(select(CommissionRecord).where(CommissionRecord.id == commission_id))
    if not record: raise HTTPException(status_code=404, detail="佣金记录不存在")
    await settle_commission(session, record); await session.commit()
    return {"message": "佣金已结算到可用余额"}

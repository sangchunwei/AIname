import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from core import alipay_service
from core.auth import AuthHandler
from core.membership_service import activate_subscription
from core.wallet_service import create_partner_commission, post_wallet_entry
from dependencies import get_session
from models.expert import ExpertOrder
from models.growth import RechargeOrder
from models.membership import VipOrder, VipPlan
from models.payment import PaymentTransaction


router = APIRouter(prefix="/payments", tags=["payments"])
auth_handler = AuthHandler()
EXPERT_PAYMENT_TIMEOUT_MINUTES = 10


def _require_alipay_config() -> None:
    missing = [
        name for name, value in {
            "AINAME_ALIPAY_APP_ID": settings.ALIPAY_APP_ID,
            "AINAME_ALIPAY_PRIVATE_KEY": settings.ALIPAY_PRIVATE_KEY,
            "AINAME_ALIPAY_PUBLIC_KEY": settings.ALIPAY_PUBLIC_KEY,
            "AINAME_ALIPAY_NOTIFY_URL": settings.ALIPAY_NOTIFY_URL,
            "AINAME_ALIPAY_RETURN_URL": settings.ALIPAY_RETURN_URL,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(status_code=500, detail=f"支付宝沙箱配置缺失: {', '.join(missing)}")


def _new_out_trade_no(prefix: str) -> str:
    return f"{prefix}{datetime.now():%Y%m%d%H%M%S}{uuid4().hex[:10].upper()}"


def _payment_response(tx: PaymentTransaction) -> dict:
    return {
        "out_trade_no": tx.out_trade_no,
        "business_type": tx.business_type,
        "business_order_id": tx.business_order_id,
        "amount_cents": tx.amount_cents,
        "status": tx.status,
        "pay_url": alipay_service.build_page_pay_url(
            out_trade_no=tx.out_trade_no,
            subject=tx.subject,
            amount_cents=tx.amount_cents,
        ) if tx.status == "pending" else None,
    }


async def _get_or_create_tx(
    session: AsyncSession,
    *,
    business_type: str,
    business_order_id: int,
    amount_cents: int,
    subject: str,
) -> PaymentTransaction:
    tx = await session.scalar(
        select(PaymentTransaction).where(
            PaymentTransaction.business_type == business_type,
            PaymentTransaction.business_order_id == business_order_id,
        )
    )
    if tx:
        if tx.amount_cents != amount_cents:
            raise HTTPException(status_code=400, detail="支付金额与原交易不一致")
        return tx
    tx = PaymentTransaction(
        out_trade_no=_new_out_trade_no({"vip": "VIP", "expert": "EXP", "recharge": "RCG"}[business_type]),
        business_type=business_type,
        business_order_id=business_order_id,
        amount_cents=amount_cents,
        subject=subject,
        status="pending",
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    return tx


@router.post("/alipay/vip/{order_id}/page-pay")
async def alipay_page_pay_vip(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    _require_alipay_config()
    order = await session.scalar(select(VipOrder).where(VipOrder.id == order_id, VipOrder.user_id == user_id))
    if not order:
        raise HTTPException(status_code=404, detail="VIP 订单不存在")
    if order.status == "paid":
        raise HTTPException(status_code=400, detail="VIP 订单已支付")
    plan = await session.scalar(select(VipPlan).where(VipPlan.id == order.plan_id))
    tx = await _get_or_create_tx(
        session,
        business_type="vip",
        business_order_id=order.id,
        amount_cents=order.amount_cents,
        subject=f"AIName VIP - {plan.name if plan else order.order_no}",
    )
    return _payment_response(tx)


@router.post("/alipay/expert/{order_id}/page-pay")
async def alipay_page_pay_expert(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    _require_alipay_config()
    order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == order_id, ExpertOrder.user_id == user_id))
    if not order:
        raise HTTPException(status_code=404, detail="专家订单不存在")
    if order.status == "pending_payment" and order.created_at and order.created_at <= datetime.now() - timedelta(minutes=EXPERT_PAYMENT_TIMEOUT_MINUTES):
        order.status = "payment_timeout"
        await session.commit()
        raise HTTPException(status_code=400, detail="订单支付超时，已自动取消")
    if order.status in {"payment_timeout", "canceled"}:
        raise HTTPException(status_code=400, detail="当前订单已取消，不能继续付款")
    if order.status != "pending_payment":
        raise HTTPException(status_code=400, detail="专家订单已支付")
    tx = await _get_or_create_tx(
        session,
        business_type="expert",
        business_order_id=order.id,
        amount_cents=order.amount_cents,
        subject=f"AIName 专家服务 - {order.selected_name}",
    )
    return _payment_response(tx)


@router.post("/alipay/recharge/{order_id}/page-pay")
async def alipay_page_pay_recharge(
    order_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    _require_alipay_config()
    order = await session.scalar(select(RechargeOrder).where(RechargeOrder.id == order_id, RechargeOrder.user_id == user_id))
    if not order:
        raise HTTPException(status_code=404, detail="充值订单不存在")
    if order.status == "paid":
        raise HTTPException(status_code=400, detail="充值订单已支付")
    tx = await _get_or_create_tx(
        session,
        business_type="recharge",
        business_order_id=order.id,
        amount_cents=order.amount_cents,
        subject=f"AIName 钱包充值 - {order.order_no}",
    )
    return _payment_response(tx)


def _notify_amount_cents(params: dict) -> int:
    try:
        return int((Decimal(str(params.get("total_amount", "0"))) * Decimal("100")).quantize(Decimal("1")))
    except (InvalidOperation, ValueError):
        return -1


async def _apply_paid_business(session: AsyncSession, tx: PaymentTransaction) -> None:
    now = datetime.now()
    if tx.business_type == "vip":
        order = await session.scalar(select(VipOrder).where(VipOrder.id == tx.business_order_id).with_for_update())
        if not order or order.amount_cents != tx.amount_cents:
            raise RuntimeError("VIP order amount mismatch")
        if order.status != "paid":
            plan = await session.scalar(select(VipPlan).where(VipPlan.id == order.plan_id))
            await activate_subscription(session, order.user_id, plan)
            order.status = "paid"
            order.payment_provider = "alipay_sandbox"
            order.paid_at = now
            await create_partner_commission(
                session, buyer_user_id=order.user_id, source_type="vip_order",
                source_order_id=order.id, gross_cents=order.amount_cents,
            )
        return

    if tx.business_type == "expert":
        order = await session.scalar(select(ExpertOrder).where(ExpertOrder.id == tx.business_order_id).with_for_update())
        if not order or order.amount_cents != tx.amount_cents:
            raise RuntimeError("Expert order amount mismatch")
        if order.status in {"payment_timeout", "canceled"}:
            raise RuntimeError("Expert order is canceled")
        if order.status == "pending_payment":
            order.status = "paid"
            order.paid_at = now
            await create_partner_commission(
                session, buyer_user_id=order.user_id, source_type="expert_order",
                source_order_id=order.id, gross_cents=order.amount_cents,
            )
        return

    if tx.business_type == "recharge":
        order = await session.scalar(select(RechargeOrder).where(RechargeOrder.id == tx.business_order_id).with_for_update())
        if not order or order.amount_cents != tx.amount_cents:
            raise RuntimeError("Recharge order amount mismatch")
        if order.status != "paid":
            await post_wallet_entry(
                session,
                user_id=order.user_id,
                entry_type="alipay_sandbox_recharge",
                available_delta=order.amount_cents,
                reference_type="recharge",
                reference_id=order.id,
                idempotency_key=f"alipay-recharge:{order.id}",
                description="支付宝沙箱充值",
            )
            order.provider = "alipay_sandbox"
            order.status = "paid"
            order.paid_at = now
        return

    raise RuntimeError("Unsupported payment business type")


async def _ensure_payment_owner(session: AsyncSession, tx: PaymentTransaction, user_id: int) -> None:
    if tx.business_type == "vip":
        order_user_id = await session.scalar(select(VipOrder.user_id).where(VipOrder.id == tx.business_order_id))
    elif tx.business_type == "expert":
        order_user_id = await session.scalar(select(ExpertOrder.user_id).where(ExpertOrder.id == tx.business_order_id))
    elif tx.business_type == "recharge":
        order_user_id = await session.scalar(select(RechargeOrder.user_id).where(RechargeOrder.id == tx.business_order_id))
    else:
        raise HTTPException(status_code=400, detail="不支持的支付业务类型")
    if order_user_id != user_id:
        raise HTTPException(status_code=404, detail="支付交易不存在")


async def _mark_transaction_paid(
    session: AsyncSession,
    tx: PaymentTransaction,
    *,
    alipay_trade_no: str | None,
    raw_notify: dict | str,
) -> None:
    if tx.status == "paid":
        return
    now = datetime.now()
    tx.status = "paid"
    tx.alipay_trade_no = alipay_trade_no or f"LOCAL_{tx.out_trade_no}"
    tx.raw_notify = raw_notify if isinstance(raw_notify, str) else json.dumps(raw_notify, ensure_ascii=False, sort_keys=True)
    tx.notified_at = now
    tx.paid_at = now
    await _apply_paid_business(session, tx)


@router.post("/alipay/notify")
async def alipay_notify(request: Request, session: AsyncSession = Depends(get_session)):
    form = await request.form()
    params = {key: str(value) for key, value in form.items()}
    try:
        verified = alipay_service.verify_signature(params)
    except Exception:
        verified = False
    if not verified:
        return PlainTextResponse("failure")
    if params.get("trade_status") not in {"TRADE_SUCCESS", "TRADE_FINISHED"}:
        return PlainTextResponse("success")

    out_trade_no = params.get("out_trade_no")
    if not out_trade_no:
        return PlainTextResponse("failure")

    try:
        async with session.begin():
            tx = await session.scalar(
                select(PaymentTransaction)
                .where(PaymentTransaction.out_trade_no == out_trade_no)
                .with_for_update()
            )
            if not tx:
                raise RuntimeError("Payment transaction not found")
            if tx.status == "paid":
                return PlainTextResponse("success")
            if tx.amount_cents != _notify_amount_cents(params):
                raise RuntimeError("Payment amount mismatch")

            await _mark_transaction_paid(
                session,
                tx,
                alipay_trade_no=params.get("trade_no"),
                raw_notify=params,
            )
    except Exception:
        return PlainTextResponse("failure")
    return PlainTextResponse("success")


@router.get("/alipay/return")
async def alipay_return(request: Request, session: AsyncSession = Depends(get_session)):
    out_trade_no = request.query_params.get("out_trade_no", "")
    params = {key: str(value) for key, value in request.query_params.items()}

    if settings.MOCK_PAYMENT_ENABLED and out_trade_no and params.get("sign"):
        try:
            verified = alipay_service.verify_signature(params)
        except Exception:
            verified = False
        if verified:
            async with session.begin():
                tx = await session.scalar(
                    select(PaymentTransaction)
                    .where(PaymentTransaction.out_trade_no == out_trade_no)
                    .with_for_update()
                )
                if tx:
                    await _mark_transaction_paid(
                        session,
                        tx,
                        alipay_trade_no=params.get("trade_no"),
                        raw_notify={**params, "source": "alipay-return-local-confirm"},
                    )

    target = f"{settings.PUBLIC_H5_URL}/#/pages/payment-result/payment-result"
    if out_trade_no:
        target = f"{target}?out_trade_no={out_trade_no}"
    return RedirectResponse(target)


@router.post("/alipay/{out_trade_no}/dev-confirm")
async def dev_confirm_alipay_payment(
    out_trade_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    if not settings.MOCK_PAYMENT_ENABLED:
        raise HTTPException(status_code=403, detail="本地确认支付仅允许在模拟支付开启时使用")

    async with session.begin():
        tx = await session.scalar(
            select(PaymentTransaction)
            .where(PaymentTransaction.out_trade_no == out_trade_no)
            .with_for_update()
        )
        if not tx:
            raise HTTPException(status_code=404, detail="支付交易不存在")
        await _ensure_payment_owner(session, tx, user_id)
        await _mark_transaction_paid(
            session,
            tx,
            alipay_trade_no=f"LOCAL_{tx.out_trade_no}",
            raw_notify={"source": "local-dev-confirm"},
        )

    return await get_payment_status(out_trade_no, session)


@router.post("/alipay/{out_trade_no}/sync")
async def sync_alipay_payment(
    out_trade_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    _require_alipay_config()
    tx = await session.scalar(select(PaymentTransaction).where(PaymentTransaction.out_trade_no == out_trade_no))
    if not tx:
        raise HTTPException(status_code=404, detail="支付交易不存在")
    await _ensure_payment_owner(session, tx, user_id)
    if tx.status == "paid":
        return await get_payment_status(out_trade_no, session)

    try:
        result = await alipay_service.query_trade(out_trade_no)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"支付宝交易查询失败: {exc}") from exc

    code = result.get("code")
    sub_code = result.get("sub_code") or ""
    trade_status = result.get("trade_status") or ""
    if code != "10000":
        return {
            **(await get_payment_status(out_trade_no, session)),
            "synced": False,
            "alipay_code": code,
            "alipay_sub_code": sub_code,
        }
    if trade_status not in {"TRADE_SUCCESS", "TRADE_FINISHED"}:
        return {
            **(await get_payment_status(out_trade_no, session)),
            "synced": False,
            "alipay_trade_status": trade_status,
        }

    if alipay_service.amount_yuan(tx.amount_cents) != str(result.get("total_amount")):
        raise HTTPException(status_code=400, detail="支付宝交易金额与本地订单金额不一致")

    await session.rollback()
    async with session.begin():
        locked_tx = await session.scalar(
            select(PaymentTransaction)
            .where(PaymentTransaction.out_trade_no == out_trade_no)
            .with_for_update()
        )
        if not locked_tx:
            raise HTTPException(status_code=404, detail="支付交易不存在")
        await _mark_transaction_paid(
            session,
            locked_tx,
            alipay_trade_no=result.get("trade_no"),
            raw_notify={**result, "source": "alipay-trade-query-sync"},
        )

    return {
        **(await get_payment_status(out_trade_no, session)),
        "synced": True,
        "alipay_trade_status": trade_status,
    }


@router.get("/{out_trade_no}")
async def get_payment_status(out_trade_no: str, session: AsyncSession = Depends(get_session)):
    tx = await session.scalar(select(PaymentTransaction).where(PaymentTransaction.out_trade_no == out_trade_no))
    if not tx:
        raise HTTPException(status_code=404, detail="支付交易不存在")
    return {
        "out_trade_no": tx.out_trade_no,
        "business_type": tx.business_type,
        "business_order_id": tx.business_order_id,
        "amount_cents": tx.amount_cents,
        "status": tx.status,
        "paid_at": tx.paid_at,
    }

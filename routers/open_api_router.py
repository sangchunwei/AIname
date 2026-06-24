import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_platform_service import (
    authenticate_api_key,
    build_internal_name_request,
    charge_successful_call,
    log_usage,
    log_failed_open_call,
    normalize_name_results,
    summarize_request,
)
from core.workflow import generate_naming_v2
from dependencies import get_session
from schemas.open_platform_schemas import OpenNameRequestIn, OpenNameResponseOut


router = APIRouter(prefix="/open/v1", tags=["open-api"])


async def generate_open_names(
    *,
    endpoint: str,
    data: OpenNameRequestIn,
    request: Request,
    session: AsyncSession,
) -> OpenNameResponseOut:
    request_id = f"req_{uuid4().hex}"
    started_at = time.perf_counter()
    client = await authenticate_api_key(session, request)
    request_summary = summarize_request(data)
    if client.app.remaining_quota < 1:
        await log_usage(
            session,
            request_id=request_id,
            app_id=client.app.id,
            api_key_id=client.api_key.id,
            endpoint=endpoint,
            status="failed",
            charged_calls=0,
            response_count=0,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            request_summary=request_summary,
            error_message="调用额度已用完",
        )
        await session.commit()
        raise HTTPException(status_code=429, detail="API 调用额度已用完")

    try:
        internal_request = build_internal_name_request(data, endpoint)
        generated = await generate_naming_v2(internal_request, client.user.id)
        raw_names = generated.get("names", {}).get("names", [])
        results = normalize_name_results(raw_names, endpoint, data)
    except HTTPException:
        raise
    except Exception as exc:
        await log_failed_open_call(
            session,
            client=client,
            request_id=request_id,
            endpoint=endpoint,
            request_summary=request_summary,
            started_at=started_at,
            error=exc,
        )
        raise HTTPException(status_code=502, detail="命名生成失败") from exc

    remaining_quota = await charge_successful_call(
        session,
        client=client,
        request_id=request_id,
        endpoint=endpoint,
        request_summary=request_summary,
        response_count=len(results),
        latency_ms=int((time.perf_counter() - started_at) * 1000),
    )
    return {
        "request_id": request_id,
        "results": results,
        "billing": {"charged_calls": 1},
        "remaining_quota": remaining_quota,
    }


@router.post("/names/game-npc", response_model=OpenNameResponseOut)
async def generate_game_npc_names(
    data: OpenNameRequestIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    return await generate_open_names(
        endpoint="game-npc",
        data=data,
        request=request,
        session=session,
    )


@router.post("/names/novel-character", response_model=OpenNameResponseOut)
async def generate_novel_character_names(
    data: OpenNameRequestIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    return await generate_open_names(
        endpoint="novel-character",
        data=data,
        request=request,
        session=session,
    )


@router.post("/names/novel-place", response_model=OpenNameResponseOut)
async def generate_novel_place_names(
    data: OpenNameRequestIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    return await generate_open_names(
        endpoint="novel-place",
        data=data,
        request=request,
        session=session,
    )

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.open_platform import DeveloperApiKey, DeveloperApp, DeveloperUsageLog
from models.user import User
from schemas.name_schemas import NameIn
from schemas.open_platform_schemas import OpenNameRequestIn, OpenNameResultOut

DEFAULT_DEMO_QUOTA = 100
DEMO_RECHARGE_QUOTA = 1000


@dataclass
class ApiClient:
    app: DeveloperApp
    api_key: DeveloperApiKey
    user: User


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return f"ak_test_{secrets.token_urlsafe(32)}"


def summarize_request(data: OpenNameRequestIn) -> str:
    text = (
        f"scenario={data.scenario}; style={data.style}; worldview={data.worldview}; "
        f"gender={data.gender}; count={data.count}; avoid={','.join(data.avoid_words)}"
    )
    return text[:1000]


def extract_api_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    header_key = request.headers.get("x-api-key", "").strip()
    if header_key:
        return header_key
    raise HTTPException(status_code=401, detail="缺少 API 密钥")


async def authenticate_api_key(session: AsyncSession, request: Request) -> ApiClient:
    raw_key = extract_api_key(request)
    key_prefix = raw_key[:16]
    key_hash = hash_api_key(raw_key)
    api_key = await session.scalar(
        select(DeveloperApiKey).where(
            DeveloperApiKey.key_prefix == key_prefix,
            DeveloperApiKey.key_hash == key_hash,
        )
    )
    if not api_key or api_key.status != "active":
        raise HTTPException(status_code=401, detail="API 密钥无效")

    app = await session.scalar(select(DeveloperApp).where(DeveloperApp.id == api_key.app_id))
    if not app or app.status != "active":
        raise HTTPException(status_code=403, detail="开发者应用已停用")

    user = await session.scalar(select(User).where(User.id == app.user_id))
    if not user or user.is_frozen or user.is_deleted:
        raise HTTPException(status_code=403, detail="开发者账号不可用")

    return ApiClient(app=app, api_key=api_key, user=user)


async def create_developer_app(session: AsyncSession, user_id: int, name: str) -> DeveloperApp:
    app = DeveloperApp(
        user_id=user_id,
        name=name,
        total_quota=DEFAULT_DEMO_QUOTA,
        remaining_quota=DEFAULT_DEMO_QUOTA,
    )
    session.add(app)
    await session.commit()
    await session.refresh(app)
    return app


async def create_api_key(session: AsyncSession, app: DeveloperApp, name: str) -> tuple[str, DeveloperApiKey]:
    raw_key = generate_api_key()
    api_key = DeveloperApiKey(
        app_id=app.id,
        name=name,
        key_prefix=raw_key[:16],
        key_tail=raw_key[-4:],
        key_hash=hash_api_key(raw_key),
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return raw_key, api_key


async def demo_recharge_app(session: AsyncSession, app: DeveloperApp) -> DeveloperApp:
    locked_app = await session.scalar(
        select(DeveloperApp).where(DeveloperApp.id == app.id).with_for_update()
    )
    locked_app.total_quota += DEMO_RECHARGE_QUOTA
    locked_app.remaining_quota += DEMO_RECHARGE_QUOTA
    await session.commit()
    await session.refresh(locked_app)
    return locked_app


async def log_usage(
    session: AsyncSession,
    *,
    request_id: str,
    app_id: int,
    api_key_id: int | None,
    endpoint: str,
    status: str,
    charged_calls: int,
    response_count: int,
    latency_ms: int,
    request_summary: str | None = None,
    error_message: str | None = None,
) -> DeveloperUsageLog:
    log = DeveloperUsageLog(
        request_id=request_id,
        app_id=app_id,
        api_key_id=api_key_id,
        endpoint=endpoint,
        status=status,
        charged_calls=charged_calls,
        response_count=response_count,
        latency_ms=latency_ms,
        request_summary=request_summary,
        error_message=(error_message or "")[:500] or None,
    )
    session.add(log)
    await session.flush()
    return log


async def charge_successful_call(
    session: AsyncSession,
    *,
    client: ApiClient,
    request_id: str,
    endpoint: str,
    request_summary: str,
    response_count: int,
    latency_ms: int,
) -> int:
    app = await session.scalar(
        select(DeveloperApp).where(DeveloperApp.id == client.app.id).with_for_update()
    )
    if not app or app.status != "active":
        raise HTTPException(status_code=403, detail="开发者应用已停用")
    if app.remaining_quota < 1:
        await log_usage(
            session,
            request_id=request_id,
            app_id=client.app.id,
            api_key_id=client.api_key.id,
            endpoint=endpoint,
            status="failed",
            charged_calls=0,
            response_count=response_count,
            latency_ms=latency_ms,
            request_summary=request_summary,
            error_message="调用额度已用完",
        )
        await session.commit()
        raise HTTPException(status_code=429, detail="API 调用额度已用完")

    app.remaining_quota -= 1
    client.api_key.last_used_at = datetime.now()
    await log_usage(
        session,
        request_id=request_id,
        app_id=app.id,
        api_key_id=client.api_key.id,
        endpoint=endpoint,
        status="success",
        charged_calls=1,
        response_count=response_count,
        latency_ms=latency_ms,
        request_summary=request_summary,
    )
    await session.commit()
    return app.remaining_quota


async def log_failed_open_call(
    session: AsyncSession,
    *,
    client: ApiClient,
    request_id: str,
    endpoint: str,
    request_summary: str,
    started_at: float,
    error: Exception,
) -> None:
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
        error_message=str(error),
    )
    await session.commit()


def build_internal_name_request(data: OpenNameRequestIn, endpoint: str) -> NameIn:
    other_parts = [
        f"OpenAPI endpoint: {endpoint}",
        f"Scenario: {data.scenario}",
        f"Style: {data.style}",
        f"Worldview: {data.worldview}",
        f"Language: {data.language}",
        f"Requested count: {data.count}",
    ]
    category = "\u4eba\u540d"
    surname = "\u4e91"
    if endpoint == "novel-place":
        category = "\u4f01\u4e1a\u540d"
        surname = ""
    return NameIn(
        category=category,
        surname=surname,
        gender=data.gender,
        length="2-4",
        other="\n".join(part for part in other_parts if part.split(": ", 1)[-1]),
        exclude=data.avoid_words,
    )


def normalize_name_results(raw_names: list, endpoint: str, data: OpenNameRequestIn) -> list[OpenNameResultOut]:
    tags = [endpoint, data.style or "general", data.language]
    results: list[OpenNameResultOut] = []
    for item in raw_names[: data.count]:
        if hasattr(item, "model_dump"):
            payload = item.model_dump()
        elif isinstance(item, dict):
            payload = item
        else:
            payload = {}
        results.append(
            OpenNameResultOut(
                name=payload.get("name", ""),
                meaning=payload.get("moral") or payload.get("meaning", ""),
                reference=payload.get("reference", ""),
                tags=[tag for tag in tags if tag],
            )
        )
    return results


async def get_usage_summary(session: AsyncSession, app: DeveloperApp, limit: int = 50):
    total_calls = await session.scalar(
        select(func.count(DeveloperUsageLog.id)).where(DeveloperUsageLog.app_id == app.id)
    )
    success_calls = await session.scalar(
        select(func.count(DeveloperUsageLog.id)).where(
            DeveloperUsageLog.app_id == app.id,
            DeveloperUsageLog.status == "success",
        )
    )
    charged_calls = await session.scalar(
        select(func.coalesce(func.sum(DeveloperUsageLog.charged_calls), 0)).where(
            DeveloperUsageLog.app_id == app.id
        )
    )
    logs = (
        await session.scalars(
            select(DeveloperUsageLog)
            .where(DeveloperUsageLog.app_id == app.id)
            .order_by(DeveloperUsageLog.id.desc())
            .limit(limit)
        )
    ).all()
    total = total_calls or 0
    success = success_calls or 0
    return {
        "total_calls": total,
        "success_calls": success,
        "failed_calls": total - success,
        "charged_calls": charged_calls or 0,
        "remaining_quota": app.remaining_quota,
        "logs": list(logs),
    }

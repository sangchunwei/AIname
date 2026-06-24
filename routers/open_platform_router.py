from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from core.open_platform_service import (
    create_api_key,
    create_developer_app,
    demo_recharge_app,
    get_usage_summary,
)
from dependencies import get_session
from models.open_platform import DeveloperApiKey, DeveloperApp
from schemas.open_platform_schemas import (
    DeveloperApiKeyCreateIn,
    DeveloperApiKeyCreateOut,
    DeveloperApiKeyOut,
    DeveloperApiKeyUpdateIn,
    DeveloperAppCreateIn,
    DeveloperAppOut,
    DeveloperUsageSummaryOut,
)


router = APIRouter(prefix="/developers", tags=["developers"])
auth_handler = AuthHandler()


async def get_owned_app(app_id: int, user_id: int, session: AsyncSession) -> DeveloperApp:
    app = await session.scalar(
        select(DeveloperApp).where(
            DeveloperApp.id == app_id,
            DeveloperApp.user_id == user_id,
            DeveloperApp.status != "deleted",
        )
    )
    if not app:
        raise HTTPException(status_code=404, detail="开发者应用不存在")
    return app


async def get_owned_key(key_id: int, user_id: int, session: AsyncSession) -> DeveloperApiKey:
    row = (
        await session.execute(
            select(DeveloperApiKey, DeveloperApp)
            .join(DeveloperApp, DeveloperApp.id == DeveloperApiKey.app_id)
            .where(
                DeveloperApiKey.id == key_id,
                DeveloperApiKey.status != "deleted",
                DeveloperApp.user_id == user_id,
                DeveloperApp.status != "deleted",
            )
        )
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="API 密钥不存在")
    api_key, _ = row
    return api_key


@router.get("/apps", response_model=list[DeveloperAppOut])
async def list_developer_apps(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return list(
        (
            await session.scalars(
                select(DeveloperApp)
                .where(DeveloperApp.user_id == user_id, DeveloperApp.status != "deleted")
                .order_by(DeveloperApp.id.desc())
            )
        ).all()
    )


@router.post("/apps", response_model=DeveloperAppOut)
async def create_app(
    data: DeveloperAppCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await create_developer_app(session, user_id, data.name)


@router.delete("/apps/{app_id}")
async def delete_app(
    app_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    app = await get_owned_app(app_id, user_id, session)
    app.status = "deleted"
    keys = (
        await session.scalars(
            select(DeveloperApiKey).where(
                DeveloperApiKey.app_id == app.id,
                DeveloperApiKey.status != "deleted",
            )
        )
    ).all()
    for api_key in keys:
        api_key.status = "deleted"
    await session.commit()
    return {"message": "开发者应用已删除"}


@router.get("/apps/{app_id}/keys", response_model=list[DeveloperApiKeyOut])
async def list_api_keys(
    app_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    app = await get_owned_app(app_id, user_id, session)
    return list(
        (
            await session.scalars(
                select(DeveloperApiKey)
                .where(DeveloperApiKey.app_id == app.id, DeveloperApiKey.status != "deleted")
                .order_by(DeveloperApiKey.id.desc())
            )
        ).all()
    )


@router.post("/apps/{app_id}/keys", response_model=DeveloperApiKeyCreateOut)
async def create_key(
    app_id: int,
    data: DeveloperApiKeyCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    app = await get_owned_app(app_id, user_id, session)
    raw_key, api_key = await create_api_key(session, app, data.name)
    return {"api_key": raw_key, "key": api_key}


@router.patch("/keys/{key_id}", response_model=DeveloperApiKeyOut)
async def rename_key(
    key_id: int,
    data: DeveloperApiKeyUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    api_key = await get_owned_key(key_id, user_id, session)
    api_key.name = data.name
    await session.commit()
    await session.refresh(api_key)
    return api_key


@router.patch("/keys/{key_id}/disable", response_model=DeveloperApiKeyOut)
async def disable_key(
    key_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    api_key = await get_owned_key(key_id, user_id, session)
    api_key.status = "disabled"
    await session.commit()
    await session.refresh(api_key)
    return api_key


@router.patch("/keys/{key_id}/enable", response_model=DeveloperApiKeyOut)
async def enable_key(
    key_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    api_key = await get_owned_key(key_id, user_id, session)
    api_key.status = "active"
    await session.commit()
    await session.refresh(api_key)
    return api_key


@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    api_key = await get_owned_key(key_id, user_id, session)
    api_key.status = "deleted"
    await session.commit()
    return {"message": "API 密钥已删除"}


@router.get("/apps/{app_id}/usage", response_model=DeveloperUsageSummaryOut)
async def get_app_usage(
    app_id: int,
    limit: int = Query(50, ge=1, le=100),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    app = await get_owned_app(app_id, user_id, session)
    return await get_usage_summary(session, app, limit)


@router.post("/apps/{app_id}/demo-recharge", response_model=DeveloperAppOut)
async def demo_recharge(
    app_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    app = await get_owned_app(app_id, user_id, session)
    return await demo_recharge_app(session, app)

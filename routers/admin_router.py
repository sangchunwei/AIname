from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.user import User
from schemas.admin_schemas import (
    AdminLoginIn,
    AdminLoginOut,
    AdminUserListOut,
    FreezeUserIn,
    ResetPasswordIn,
)


router = APIRouter(prefix="/admin", tags=["admin"])
auth_handler = AuthHandler()


async def require_admin(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
) -> User:
    admin = await session.scalar(select(User).where(User.id == int(user_id)))
    if not admin or not admin.is_admin or admin.is_frozen or admin.is_deleted:
        raise HTTPException(status_code=403, detail="管理员权限无效")
    return admin


async def get_normal_user_or_404(user_id: int, session: AsyncSession) -> User:
    user = await session.scalar(
        select(User).where(User.id == user_id, User.is_admin.is_(False), User.is_deleted.is_(False))
    )
    if not user:
        raise HTTPException(status_code=404, detail="普通用户不存在")
    return user


@router.post("/login", response_model=AdminLoginOut)
async def admin_login(data: AdminLoginIn, session: AsyncSession = Depends(get_session)):
    admin = await session.scalar(select(User).where(User.email == data.email))
    if not admin or not admin.is_admin or admin.is_deleted:
        raise HTTPException(status_code=401, detail="管理员账号或密码错误")
    if admin.is_frozen:
        raise HTTPException(status_code=403, detail="管理员账号已被冻结")
    if not admin.check_password(data.password):
        raise HTTPException(status_code=401, detail="管理员账号或密码错误")

    token = auth_handler.encode_login_token(admin.id, admin.token_version)["access_token"]
    return {"admin": admin, "token": token}


@router.get("/users", response_model=AdminUserListOut)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query("", max_length=100),
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    filters = [User.is_admin.is_(False), User.is_deleted.is_(False)]
    if keyword.strip():
        pattern = f"%{keyword.strip()}%"
        filters.append(or_(User.email.like(pattern), User.username.like(pattern)))

    total = await session.scalar(select(func.count(User.id)).where(*filters))
    users = (
        await session.scalars(
            select(User)
            .where(*filters)
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return {"total": total or 0, "page": page, "page_size": page_size, "users": users}


@router.patch("/users/{user_id}/freeze")
async def freeze_user(
    user_id: int,
    data: FreezeUserIn,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await get_normal_user_or_404(user_id, session)
    user.is_frozen = data.is_frozen
    if data.is_frozen:
        user.token_version += 1
    await session.commit()
    return {"message": "账号已冻结" if data.is_frozen else "账号已解冻"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    data: ResetPasswordIn,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await get_normal_user_or_404(user_id, session)
    user.password = data.new_password
    user.token_version += 1
    await session.commit()
    return {"message": "密码重置成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    from datetime import datetime

    user = await get_normal_user_or_404(user_id, session)
    user.is_deleted = True
    user.is_frozen = True
    user.token_version += 1
    user.deleted_at = datetime.now()
    await session.commit()
    return {"message": "账号已删除"}

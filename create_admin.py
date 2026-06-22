"""通过环境变量创建或提升管理员账号。

PowerShell 示例：
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="请使用强密码"
$env:ADMIN_USERNAME="系统管理员"
python create_admin.py
"""
import asyncio
import os

from sqlalchemy import select

from models import AsyncSessionFactory
from models.user import User


async def create_admin():
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    username = os.getenv("ADMIN_USERNAME", "系统管理员")
    if not email or not password or len(password) < 8:
        raise ValueError("请设置 ADMIN_EMAIL 和至少 8 位的 ADMIN_PASSWORD 环境变量")

    async with AsyncSessionFactory() as session:
        user = await session.scalar(select(User).where(User.email == email))
        if user:
            user.username = username
            user.password = password
            user.is_admin = True
            user.is_frozen = False
            user.is_deleted = False
            user.deleted_at = None
        else:
            user = User(email=email, username=username, password=password, is_admin=True)
            session.add(user)
        await session.commit()
        print(f"管理员账号已就绪：{email}")


if __name__ == "__main__":
    asyncio.run(create_admin())

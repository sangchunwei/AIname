from core.mailtools import create_mail_instance
from fastapi_mail import FastMail

async def get_mail():
    return create_mail_instance()

from models import AsyncSessionFactory

#对会话工程的权限发放和收回
async def get_session():
    session=AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()
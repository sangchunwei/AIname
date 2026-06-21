from fastapi_mail import FastMail,ConnectionConfig
from pydantic import SecretStr,EmailStr
import settings

def create_mail_instance()->FastMail:
    config = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=True,#启用 STARTTLS 协议
        MAIL_SSL_TLS=False,#不直接使用隐式 SSL/TLS 连接
        USE_CREDENTIALS=True,#发送邮件时需要提供用户名和密码进行身份验证
        VALIDATE_CERTS=True#严格验证服务器的 SSL/TLS 证书
    )
    return FastMail(config)
import random
import string

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from fastapi_mail import FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from dependencies import get_mail,get_session
from repository.user_repo import EmailCodeRepository
from  core.redisconfig import get_redis_client
from   redis.asyncio.client import Redis

router = APIRouter(prefix="/auth",tags=["auth"])

#发送验证码给客户

@router.get("/code")
async def get_email_code(email:Annotated[EmailStr,Query(...)],fastmail:FastMail=Depends(get_mail),session:AsyncSession=Depends(get_session),redis:Redis=Depends(get_redis_client)):
    #1.生成验证码   digits="0123456789"
    source = string.digits*4
    #simple 随机取元素,返回的是列表
    #join拼接为字符串
    code="".join(random.sample(source,4))
    #2.创建一个邮件
    message=MessageSchema(
        subject="app[ainame]验证码",  # 主题
        recipients=[email],  # 接收者
        body=f"验证码为{code},五分钟后失效",
        subtype=MessageType.plain#纯文本格式
    )
    #3.发送邮件
    await fastmail.send_message(message)
    #4.把发送的邮件信息保存
    # email_repository = EmailCodeRepository(session=session)#将会话权限交给类,使得变量获得会话权限
    # await email_repository.create_email_code(email,code)

    #redis存储的key和value,key是我们设计的,所以取值时需要用相同的规则
    await redis.set(email,code,300)
    return {"message":"验证码发送成功"}


from schemas.user_schemas import RegisterIn, UserCreateSchema, LoginIn
from repository.user_repo import UserRepository

# 功能: 用户注册  本质上就是向用户表插入一条数据
# 用户在页面上填写信息
# 后台接收用户信息,可以设计对象接受,把接收的对象转为数据库对象,填入数据库
@router.post("/register")
async def register(userinfo:RegisterIn,session:AsyncSession=Depends(get_session),redis:Redis=Depends(get_redis_client)):
    #向用户表插入数据
    userRepository = UserRepository(session=session)
    #用户传过来的信息中需要一些校验
    #1.邮箱是否已经被别人注册了
    email_exists=await userRepository.email_is_exist(userinfo.email)
    if email_exists:
        raise HTTPException(status_code=400,detail="该邮箱已被注册,请直接登录")
    #2.校验验证码是否正确
    # email_code_bool=await EmailCodeRepository(session=session).check_email_code(userinfo.email,userinfo.code)
    # if not email_code_bool:
    #     raise HTTPException(status_code=400,detail="验证码错误或失效")

    email_code=await redis.get(userinfo.email)
    if (not email_code) or (userinfo.code != email_code):
        raise HTTPException(400,detail="验证码错误或者已过期")

    #3.允许注册    (插入一条用户数据到数据库)
    await userRepository.create_user(UserCreateSchema(email=userinfo.email,username=userinfo.username,password=userinfo.password))

    #注册成功,删除redis中的数据,防止重新注册
    await redis.delete(userinfo.email)
    return {"message":"注册成功,请登录"}

from  models.user import User
from core.auth import AuthHandler
from schemas.user_schemas import LoginOut
authHandler = AuthHandler()
#登录
@router.post("/login",response_model=LoginOut)
async def login(userinfo:LoginIn,session:AsyncSession=Depends(get_session)):
    #获取你的信息,邮箱,根据邮箱才能知道你是否是会员
    #1.因为你想登录,我们需要确认你是否已经注册,未注册不能登录
    userRepository = UserRepository(session=session)
    #数据库查询
    user:User|None = await userRepository.get_user_by_email(userinfo.email)
    if not user:
        raise HTTPException(status_code=400,detail="该用户不存在!")
    if user.is_deleted:
        raise HTTPException(status_code=400,detail="该用户不存在!")
    if user.is_admin:
        raise HTTPException(status_code=403,detail="管理员账号请从管理员入口登录")
    if user.is_frozen:
        raise HTTPException(status_code=403,detail="账号已被冻结，请联系管理员")
    #2.看密码对不对
    if not user.check_password(userinfo.password):
        raise HTTPException(status_code=400,detail="密码错误,请重新输入")
    #3.密码正确允许登录.登录的方法是给用户返回一个令牌,用户拿着这个令牌,下次来证明已经登陆过了
    tokens=authHandler.encode_login_token(user.id, user.token_version)
    return {
        "user":user,
        "token":tokens['access_token']
    }

from mako.testing.helpers import result_lines
from sqlalchemy.ext.asyncio.session import AsyncSession
from models.user import User, EmailCode
from sqlalchemy import select, update, delete, exists
from datetime import datetime, timedelta

from schemas.user_schemas import UserCreateSchema


#与email交互
class EmailCodeRepository():
    def __init__(self,session: AsyncSession):
        self.session = session
    #把一条emailcode数据插入到数据库中
    async def create_email_code(self,email:str,code:str):
        async with self.session.begin():
            #准备与email_code表对应的一个对象
            email_code = EmailCode(email=email,code=code)
            self.session.add(email_code)

            return email_code

    #验证验证码
    async def check_email_code(self,email:str,code:str):
        async with self.session.begin():
            #filter过滤多条数据
            email_code=await self.session.scalar(select(EmailCode).filter(EmailCode.email==email,EmailCode.code==code))
            # 数据库如果没有email_code这个类证明没有发送验证码或者验证码不正确
            if not email_code:
                return False
            #如果超过了5分钟则失效
            if(datetime.now() - email_code.created_time) >= timedelta(minutes=5):
                return False
            return True


#与user表交互的对象
class UserRepository():
    def __init__(self,session: AsyncSession):
        self.session = session
    #我判断用户传来的邮箱是否已被注册
    async def get_user_by_email(self,email:str):
        async with self.session.begin():
            result=await self.session.execute(select(User).filter(User.email==email))
            return result.scalar_one_or_none()

    async def get_user_by_id(self,user_id:int):
        async with self.session.begin():
            return await self.session.scalar(select(User).filter(User.id==user_id))

    #插入一条数据
    async def create_user(self,user:UserCreateSchema):
        async with self.session.begin():
            #user.model_dump() 将对象属性数据变成字典
            #**解包   User(email="xx.qq.com",username="")
            user = User(**user.model_dump())
            self.session.add(user)
            return user

    # 我判断用户传来的邮箱是否已被注册
    async def email_is_exist(self,mail:str):
        async with self.session.begin():
            stmt = select(exists().where(User.email==mail))
            return await self.session.scalar(stmt)

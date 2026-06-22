from . import Base
# SQLAlchemy 负责 操作数据库(操作)
# Alembic 负责 管理数据库结构的变化(执行)
from sqlalchemy.orm import Mapped,mapped_column#sqlaichemy数据库工具库之一,让 Python 程序操作数据库，而不用到处手写 SQL。orm 关系映射层
from sqlalchemy import Integer,String,DateTime,Boolean#核心层,偏向于SQL
from pwdlib import PasswordHash#哈希加密
from datetime import datetime

password_hash=PasswordHash.recommended()
class User(Base):
    __tablename__ = 'user'

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100),unique=True)
    username:Mapped[str] = mapped_column(String(100))
    #数据库存储的是加密后的密码,不是明文密码
    #私有化,
    _password:Mapped[str] = mapped_column(String(200))
    is_admin:Mapped[bool] = mapped_column(Boolean,default=False,server_default="0")
    is_frozen:Mapped[bool] = mapped_column(Boolean,default=False,server_default="0")
    is_deleted:Mapped[bool] = mapped_column(Boolean,default=False,server_default="0")
    token_version:Mapped[int] = mapped_column(Integer,default=0,server_default="0")
    created_at:Mapped[datetime] = mapped_column(DateTime,default=datetime.now)
    deleted_at:Mapped[datetime|None] = mapped_column(DateTime,nullable=True)

    #1.校验数据:密码是否正确
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)#初始化父类
        password=kwargs.pop('password',None)#取出password,在kwargs的最后没有则取none,同时在kwargs中删除
        if password:
            #增加一个变量 password  设置password会自动调用@@password.setter
            self.password=password  #不是给实例增加一个普通属性，而是触发 @password.setter 方法进行密码加密处理。

    @property   #凡是获取password时调用
    def password(self):
        return self._password
    #不是函数重载,更像是给函数加载新配置
    @password.setter    #无论何时设置password时,都会将传入的password加密,默认调用
    def password(self,password):
        self._password=password_hash.hash(password)

    def check_password(self,password):  #校验密码
        return password_hash.verify(password,self._password)



class EmailCode(Base):
    __tablename__ = 'email_code'

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100))
    code:Mapped[str] = mapped_column(String(100))
    #发送的验证码有时效
    created_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now())

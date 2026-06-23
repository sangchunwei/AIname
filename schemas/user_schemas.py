from typing import Annotated
from pydantic import BaseModel, Field, EmailStr, model_validator, ValidationError

#接收用户传过来的数据的一个对象
RawPasswordStr=Annotated[str,Field(...,min_length=4,max_length=50)]
RawUsernameStr=Annotated[str,Field(...,min_length=4,max_length=50)]
class RegisterIn(BaseModel):
    email: EmailStr#pydantic中的email数据类型对象
    username: RawUsernameStr
    password:RawPasswordStr
    confirm_password:RawPasswordStr#确认密码
    #验证用户有效性
    code:Annotated[str,Field(...,min_length=4,max_length=4)]
    invite_code: str | None = Field(default=None, max_length=32)

    #完成确认密码的校验
    @model_validator(mode="after")
    def password_id_valid(self,password:str)->bool:
        password=self.password
        confirm_password=self.confirm_password
        if  password != confirm_password:
            raise ValidationError("Passwords don't match")
        return self

#存入数据库的是少数字段
class UserCreateSchema(BaseModel):
    email: EmailStr
    username: RawUsernameStr
    password: RawPasswordStr

#开发对象,接受用户登录信息
class LoginIn(BaseModel):
    email: EmailStr
    password: RawPasswordStr

class UserSchema(BaseModel):
    id: Annotated[int,Field(...)]
    email: EmailStr
    # 昵称可在个人中心修改，不再套用注册时“至少 4 位”的用户名规则。
    username: str

class LoginOut(BaseModel):
    user: UserSchema
    token:str

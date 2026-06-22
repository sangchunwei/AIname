from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, max_length=50)


class AdminInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str


class AdminLoginOut(BaseModel):
    admin: AdminInfo
    token: str


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    is_frozen: bool
    created_at: datetime


class AdminUserListOut(BaseModel):
    total: int
    page: int
    page_size: int
    users: list[AdminUserOut]


class ResetPasswordIn(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=50)


class FreezeUserIn(BaseModel):
    is_frozen: bool

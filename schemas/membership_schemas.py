from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileUpdateIn(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    bio: str | None = Field(default=None, max_length=500)


class DefaultAvatarSelectIn(BaseModel):
    avatar_key: str = Field(..., min_length=1, max_length=30)


class PasswordChangeIn(BaseModel):
    current_password: str = Field(..., min_length=4, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)
    confirm_password: str = Field(..., min_length=6, max_length=50)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise ValueError("两次输入的新密码不一致")
        if self.new_password == self.current_password:
            raise ValueError("新密码不能与当前密码相同")
        return self


class VipPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: str | None
    price_cents: int
    duration_days: int
    daily_name_limit: int
    daily_visual_limit: int


class SubscriptionOut(BaseModel):
    is_vip: bool
    plan_name: str | None = None
    expires_at: datetime | None = None


class UsageOut(BaseModel):
    name_used: int
    name_limit: int
    visual_used: int
    visual_limit: int


class UserCenterOut(BaseModel):
    id: int
    email: str
    username: str
    avatar_url: str | None
    bio: str | None
    created_at: datetime
    is_expert: bool
    subscription: SubscriptionOut
    usage: UsageOut


class VipOrderCreateIn(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=50)


class VipOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_no: str
    amount_cents: int
    status: str
    payment_provider: str
    paid_at: datetime | None
    created_at: datetime


class VipGrantIn(BaseModel):
    user_id: int
    plan_code: str = Field(..., min_length=1, max_length=50)

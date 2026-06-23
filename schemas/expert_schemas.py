from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExpertVerifyIn(BaseModel):
    user_id: int
    display_name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=100)
    bio: str = Field(..., min_length=10, max_length=3000)
    avatar_url: str | None = Field(default=None, max_length=500)


class ExpertServiceCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=10, max_length=3000)
    price_cents: int = Field(..., ge=100, le=10000000)
    delivery_days: int = Field(default=3, ge=1, le=60)


class ExpertServiceOut(BaseModel):
    id: int
    expert_id: int
    expert_name: str
    expert_title: str
    category: str
    name: str
    description: str
    price_cents: int
    delivery_days: int


class ExpertOrderCreateIn(BaseModel):
    service_id: int
    selected_name: str = Field(..., min_length=1, max_length=100)
    requirements: str = Field(..., min_length=5, max_length=5000)


class ExpertOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    service_id: int
    expert_id: int
    selected_name: str
    requirements: str
    amount_cents: int
    status: str
    ai_draft: str | None
    final_report: str | None
    paid_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime


class ExpertReportIn(BaseModel):
    final_report: str = Field(..., min_length=50, max_length=30000)

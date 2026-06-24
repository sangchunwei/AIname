from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeveloperAppCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class DeveloperAppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    total_quota: int
    remaining_quota: int
    created_at: datetime
    updated_at: datetime


class DeveloperApiKeyCreateIn(BaseModel):
    name: str = Field("默认 API 密钥", min_length=1, max_length=100)


class DeveloperApiKeyUpdateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class DeveloperApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    name: str
    key_prefix: str
    key_tail: str
    status: str
    last_used_at: datetime | None
    created_at: datetime


class DeveloperApiKeyCreateOut(BaseModel):
    api_key: str
    key: DeveloperApiKeyOut


class DeveloperUsageLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    app_id: int
    api_key_id: int | None
    endpoint: str
    status: str
    charged_calls: int
    response_count: int
    latency_ms: int
    request_summary: str | None
    error_message: str | None
    created_at: datetime


class DeveloperUsageSummaryOut(BaseModel):
    total_calls: int
    success_calls: int
    failed_calls: int
    charged_calls: int
    remaining_quota: int
    logs: list[DeveloperUsageLogOut]


class OpenNameRequestIn(BaseModel):
    scenario: str = Field("", max_length=300)
    style: str = Field("", max_length=100)
    worldview: str = Field("", max_length=500)
    gender: Literal["不限", "男", "女"] = "不限"
    count: int = Field(5, ge=1, le=10)
    avoid_words: list[str] = Field(default_factory=list, max_length=20)
    language: str = Field("zh-CN", max_length=20)


class OpenNameResultOut(BaseModel):
    name: str
    meaning: str
    reference: str
    tags: list[str] = Field(default_factory=list)


class OpenBillingOut(BaseModel):
    charged_calls: int


class OpenNameResponseOut(BaseModel):
    request_id: str
    results: list[OpenNameResultOut]
    billing: OpenBillingOut
    remaining_quota: int

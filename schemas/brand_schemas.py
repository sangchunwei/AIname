from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BrandProjectCreate(BaseModel):
    selected_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="企业名", max_length=30)
    name_reference: str | None = Field(default=None, max_length=2000)
    name_moral: str | None = Field(default=None, max_length=2000)
    industry: str = Field(..., min_length=1, max_length=100)
    audience: str | None = Field(default=None, max_length=200)
    style: str = Field(default="现代简约", max_length=100)
    color_preference: str | None = Field(default=None, max_length=100)


class BrandProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    selected_name: str
    category: str
    name_reference: str | None
    name_moral: str | None
    industry: str
    audience: str | None
    style: str
    color_preference: str | None
    brand_brief: str | None
    visual_keywords: str | None
    created_at: datetime
    updated_at: datetime


class BrandSloganOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    rationale: str | None
    is_selected: bool


class VisualAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_type: str
    file_url: str
    prompt: str
    created_at: datetime


class BrandProjectDetailOut(BrandProjectOut):
    slogans: list[BrandSloganOut] = Field(default_factory=list)
    assets: list[VisualAssetOut] = Field(default_factory=list)


class BrandStrategyOut(BaseModel):
    project: BrandProjectOut
    slogans: list[BrandSloganOut]


class VisualGenerateIn(BaseModel):
    asset_type: Literal["logo", "business_card"] = "logo"
    count: int = Field(default=4, ge=1, le=4)
    slogan_id: int | None = None


class VisualJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    asset_type: str
    status: str
    requested_count: int
    provider: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    assets: list[VisualAssetOut] = Field(default_factory=list)


class SloganIdea(BaseModel):
    text: str = Field(..., max_length=100)
    rationale: str = Field(..., max_length=500)


class BrandStrategyResult(BaseModel):
    brand_brief: str = Field(..., max_length=1000)
    visual_keywords: list[str] = Field(..., min_length=3, max_length=8)
    slogans: list[SloganIdea] = Field(..., min_length=3, max_length=5)

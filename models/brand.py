from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class BrandProject(Base):
    __tablename__ = "brand_project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    selected_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(30), default="企业名")
    name_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_moral: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str] = mapped_column(String(100))
    audience: Mapped[str | None] = mapped_column(String(200), nullable=True)
    style: Mapped[str] = mapped_column(String(100), default="现代简约")
    color_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brand_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class BrandSlogan(Base):
    __tablename__ = "brand_slogan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("brand_project.id"), index=True)
    text: Mapped[str] = mapped_column(String(200))
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class VisualGenerationJob(Base):
    __tablename__ = "visual_generation_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("brand_project.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    requested_count: Mapped[int] = mapped_column(Integer, default=4)
    prompt: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class VisualAsset(Base):
    __tablename__ = "visual_asset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("brand_project.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("visual_generation_job.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(30))
    file_url: Mapped[str] = mapped_column(String(500))
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from core.brand_service import build_visual_prompt, generate_brand_strategy
from core.visual_provider import get_visual_provider
from core.visual_worker import enqueue_visual_job
from core.membership_service import ensure_quota, consume_quota
from dependencies import get_session
from models.brand import BrandProject, BrandSlogan, VisualAsset, VisualGenerationJob
from schemas.brand_schemas import (
    BrandProjectCreate,
    BrandProjectDetailOut,
    BrandProjectOut,
    BrandStrategyOut,
    VisualGenerateIn,
    VisualJobOut,
)


router = APIRouter(prefix="/brands", tags=["品牌视觉"])
auth_handler = AuthHandler()


async def get_owned_project(project_id: int, user_id: int, session: AsyncSession) -> BrandProject:
    project = await session.scalar(
        select(BrandProject).where(BrandProject.id == project_id, BrandProject.user_id == user_id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="品牌项目不存在")
    return project


async def build_project_detail(project: BrandProject, session: AsyncSession) -> BrandProjectDetailOut:
    slogans = (
        await session.scalars(
            select(BrandSlogan).where(BrandSlogan.project_id == project.id).order_by(BrandSlogan.id)
        )
    ).all()
    assets = (
        await session.scalars(
            select(VisualAsset).where(VisualAsset.project_id == project.id).order_by(VisualAsset.id.desc())
        )
    ).all()
    data = BrandProjectOut.model_validate(project).model_dump()
    return BrandProjectDetailOut(**data, slogans=list(slogans), assets=list(assets))


async def build_job_output(job: VisualGenerationJob, session: AsyncSession) -> VisualJobOut:
    assets = (
        await session.scalars(select(VisualAsset).where(VisualAsset.job_id == job.id).order_by(VisualAsset.id))
    ).all()
    data = {
        "id": job.id,
        "project_id": job.project_id,
        "asset_type": job.asset_type,
        "status": job.status,
        "requested_count": job.requested_count,
        "provider": job.provider,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "assets": list(assets),
    }
    return VisualJobOut(**data)


@router.post("", response_model=BrandProjectOut)
async def create_brand_project(
    data: BrandProjectCreate,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project = BrandProject(user_id=user_id, **data.model_dump())
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.get("", response_model=list[BrandProjectOut])
async def list_brand_projects(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return list(
        (
            await session.scalars(
                select(BrandProject)
                .where(BrandProject.user_id == user_id)
                .order_by(BrandProject.id.desc())
            )
        ).all()
    )


@router.get("/visual-jobs/{job_id}", response_model=VisualJobOut)
async def get_visual_job(
    job_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    job = await session.scalar(
        select(VisualGenerationJob)
        .join(BrandProject, BrandProject.id == VisualGenerationJob.project_id)
        .where(VisualGenerationJob.id == job_id, BrandProject.user_id == user_id)
    )
    if not job:
        raise HTTPException(status_code=404, detail="视觉生成任务不存在")
    return await build_job_output(job, session)


@router.get("/{project_id}", response_model=BrandProjectDetailOut)
async def get_brand_project(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project = await get_owned_project(project_id, user_id, session)
    return await build_project_detail(project, session)


@router.post("/{project_id}/strategy", response_model=BrandStrategyOut)
async def create_brand_strategy(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project = await get_owned_project(project_id, user_id, session)
    try:
        result = await generate_brand_strategy(project)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="品牌策略生成失败，请稍后重试") from exc

    project.brand_brief = result.brand_brief
    project.visual_keywords = "、".join(result.visual_keywords)
    await session.execute(delete(BrandSlogan).where(BrandSlogan.project_id == project.id))
    slogans = [
        BrandSlogan(project_id=project.id, text=item.text, rationale=item.rationale)
        for item in result.slogans
    ]
    session.add_all(slogans)
    await session.commit()
    await session.refresh(project)
    for slogan in slogans:
        await session.refresh(slogan)
    return {"project": project, "slogans": slogans}


@router.post("/{project_id}/visuals", response_model=VisualJobOut)
async def create_visuals(
    project_id: int,
    data: VisualGenerateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project = await get_owned_project(project_id, user_id, session)
    await ensure_quota(session, user_id, "visual_generation")
    if not project.brand_brief:
        raise HTTPException(status_code=400, detail="请先生成品牌策略")

    slogan_text = None
    if data.slogan_id is not None:
        slogan = await session.scalar(
            select(BrandSlogan).where(
                BrandSlogan.id == data.slogan_id,
                BrandSlogan.project_id == project.id,
            )
        )
        if not slogan:
            raise HTTPException(status_code=400, detail="所选 Slogan 不属于当前项目")
        slogan_text = slogan.text

    prompt = build_visual_prompt(project, data.asset_type, slogan_text)
    provider = get_visual_provider()
    job = VisualGenerationJob(
        project_id=project.id,
        asset_type=data.asset_type,
        status="queued",
        requested_count=data.count,
        prompt=prompt,
        provider=provider.name,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    try:
        await enqueue_visual_job(job.id, slogan_text)
    except Exception as exc:
        job.status = "failed"
        job.error_message = "视觉任务队列暂时不可用"
        await session.commit()
        raise HTTPException(status_code=503, detail="视觉任务队列暂时不可用") from exc
    await consume_quota(session, user_id, "visual_generation")
    return await build_job_output(job, session)

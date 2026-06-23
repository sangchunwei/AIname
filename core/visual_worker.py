import asyncio
import json
from contextlib import suppress

from sqlalchemy import select

from core.redisconfig import redis_client
from core.visual_provider import get_visual_provider
from models import AsyncSessionFactory
from models.brand import BrandProject, VisualAsset, VisualGenerationJob


QUEUE_KEY = "ainame:brand_visual_jobs"
worker_task: asyncio.Task | None = None


async def enqueue_visual_job(job_id: int, slogan_text: str | None = None) -> None:
    payload = json.dumps({"job_id": job_id, "slogan_text": slogan_text}, ensure_ascii=False)
    await redis_client.rpush(QUEUE_KEY, payload)


async def run_visual_job(job_id: int, slogan_text: str | None = None) -> None:
    async with AsyncSessionFactory() as session:
        try:
            job = await session.scalar(select(VisualGenerationJob).where(VisualGenerationJob.id == job_id))
            if not job or job.status == "completed":
                return
            project = await session.scalar(select(BrandProject).where(BrandProject.id == job.project_id))
            if not project:
                raise RuntimeError("品牌项目不存在")

            job.status = "running"
            await session.commit()
            provider = get_visual_provider()
            file_urls = await provider.generate(
                prompt=job.prompt,
                count=job.requested_count,
                asset_type=job.asset_type,
                brand_name=project.selected_name,
                slogan=slogan_text,
            )
            session.add_all(
                [
                    VisualAsset(
                        project_id=project.id,
                        job_id=job.id,
                        asset_type=job.asset_type,
                        file_url=file_url,
                        prompt=job.prompt,
                    )
                    for file_url in file_urls
                ]
            )
            job.status = "completed"
            job.error_message = None
            await session.commit()
        except Exception as exc:
            await session.rollback()
            job = await session.scalar(select(VisualGenerationJob).where(VisualGenerationJob.id == job_id))
            if job:
                job.status = "failed"
                job.error_message = str(exc)[:1000]
                await session.commit()


async def visual_worker_loop() -> None:
    while True:
        try:
            item = await redis_client.blpop(QUEUE_KEY, timeout=5)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(2)
            continue
        if not item:
            continue
        try:
            payload = json.loads(item[1])
            await run_visual_job(int(payload["job_id"]), payload.get("slogan_text"))
        except asyncio.CancelledError:
            await redis_client.rpush(QUEUE_KEY, item[1])
            raise
        except Exception:
            # 单个异常任务不能终止整个消费者；任务自身错误会记录到数据库。
            continue


async def start_visual_worker() -> None:
    global worker_task
    if worker_task is None or worker_task.done():
        worker_task = asyncio.create_task(visual_worker_loop(), name="brand-visual-worker")


async def stop_visual_worker() -> None:
    global worker_task
    if worker_task:
        worker_task.cancel()
        with suppress(asyncio.CancelledError):
            await worker_task
        worker_task = None

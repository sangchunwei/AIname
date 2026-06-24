from fastapi import APIRouter, Query
from pydantic import BaseModel

import settings


router = APIRouter(prefix="/app", tags=["app-version"])


class AppVersionOut(BaseModel):
    platform: str
    current_version_code: int
    latest_version_name: str
    latest_version_code: int
    has_update: bool
    force_update: bool
    download_url: str
    release_notes: str


@router.get("/version", response_model=AppVersionOut)
async def get_app_version(
    platform: str = Query("app", description="Client platform, such as android or ios"),
    version_code: int = Query(0, ge=0, description="Current client versionCode"),
):
    has_update = settings.APP_UPDATE_ENABLED and version_code < settings.APP_LATEST_VERSION_CODE
    force_update = has_update and version_code < settings.APP_MIN_VERSION_CODE
    return AppVersionOut(
        platform=platform,
        current_version_code=version_code,
        latest_version_name=settings.APP_LATEST_VERSION_NAME,
        latest_version_code=settings.APP_LATEST_VERSION_CODE,
        has_update=has_update,
        force_update=force_update,
        download_url=settings.APP_UPDATE_URL,
        release_notes=settings.APP_RELEASE_NOTES,
    )

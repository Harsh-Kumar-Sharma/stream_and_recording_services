from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.http import is_http_reachable
from app.services.storage_service import StorageService

router = APIRouter(tags=["health"])


@router.get("/health")
async def basic_health() -> dict:
    settings = get_settings()
    return {
        "status": True,
        "service": settings.app.name,
        "environment": settings.app.environment,
    }


@router.get("/api/v1/health")
async def detailed_health(request: Request) -> dict:
    settings = get_settings()
    stream_service = getattr(request.app.state, "stream_service", None)
    recording_service = getattr(request.app.state, "recording_service", None)
    storage_service = getattr(request.app.state, "storage_service", None) or StorageService(settings)
    return {
        "status": True,
        "service": settings.app.name,
        "environment": settings.app.environment,
        "activeStreams": stream_service.active_count() if stream_service else 0,
        "activeRecorders": recording_service.active_count() if recording_service else 0,
        "storageRoot": str(settings.recording.storage_root),
        "storageMinFreeDiskPercent": settings.storage.min_free_disk_percent,
        "storageFreePercent": storage_service.free_disk_percent(),
        "mediamtx": {
            "configured": bool(settings.mediamtx.base_url),
            "reachable": await is_http_reachable(settings.mediamtx.base_url),
        },
        "javaApi": {
            "configured": bool(settings.java_api.base_url),
            "reachable": await is_http_reachable(settings.java_api.base_url),
        },
    }

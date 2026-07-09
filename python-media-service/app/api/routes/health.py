from fastapi import APIRouter, Request

from app.core.config import get_settings

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
    return {
        "status": True,
        "service": settings.app.name,
        "environment": settings.app.environment,
        "activeStreams": stream_service.active_count() if stream_service else 0,
        "activeRecorders": recording_service.active_count() if recording_service else 0,
        "storageRoot": str(settings.recording.storage_root),
        "storageMinFreeDiskPercent": settings.storage.min_free_disk_percent,
        "mediamtxConfigured": bool(settings.mediamtx.public_hls_base_url),
        "javaApiConfigured": bool(settings.java_api.base_url),
    }

from datetime import datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.exceptions import MediaServiceError
from app.middleware.auth_middleware import error_response
from app.services.playback_service import PlaybackService

router = APIRouter(prefix="/api/v1/playback", tags=["playback"])


def get_playback_service(request: Request) -> PlaybackService:
    service = getattr(request.app.state, "playback_service", None)
    if service is None:
        service = PlaybackService(get_settings())
        request.app.state.playback_service = service
    return service


@router.get("/search")
async def search_playback(
    request: Request,
    cameraId: str,
    from_time: datetime | None = Query(default=None, alias="from"),
    to_time: datetime | None = Query(default=None, alias="to"),
) -> dict:
    try:
        return get_playback_service(request).search(cameraId, from_time, to_time)
    except MediaServiceError as exc:
        return error_response(exc.status_code, exc.message, exc.error_code)


@router.get("/{camera_id}/files")
async def list_camera_files(camera_id: str, request: Request, date: str | None = None) -> dict:
    try:
        return get_playback_service(request).list_files(camera_id, date)
    except MediaServiceError as exc:
        return error_response(exc.status_code, exc.message, exc.error_code)


@router.get("/{camera_id}/file")
async def serve_playback_file(camera_id: str, request: Request, path: str):
    try:
        file_path = get_playback_service(request).resolve_file_token(camera_id, path)
        return FileResponse(file_path, media_type="video/mp4", filename=file_path.name)
    except MediaServiceError as exc:
        return error_response(exc.status_code, exc.message, exc.error_code)

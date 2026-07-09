from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.exceptions import MediaServiceError
from app.middleware.auth_middleware import error_response
from app.services.recording_service import RecordingService

router = APIRouter(prefix="/api/v1/recorders", tags=["recorders"])


def get_recording_service(request: Request) -> RecordingService:
    service = getattr(request.app.state, "recording_service", None)
    if service is None:
        service = RecordingService(get_settings())
        request.app.state.recording_service = service
    return service


@router.post("/{camera_id}/start")
async def start_recording(camera_id: str, request: Request) -> dict:
    try:
        state = await get_recording_service(request).start_recording(camera_id, request.state.bearer_token)
        return state.to_response()
    except MediaServiceError as exc:
        return error_response(exc.status_code, exc.message, exc.error_code)


@router.post("/{camera_id}/stop")
async def stop_recording(camera_id: str, request: Request) -> dict:
    return await get_recording_service(request).stop_recording(camera_id)


@router.get("/{camera_id}/status")
async def recording_status(camera_id: str, request: Request) -> dict:
    return await get_recording_service(request).get_status(camera_id)


@router.get("")
async def list_recorders(request: Request) -> dict:
    return await get_recording_service(request).list_recordings()

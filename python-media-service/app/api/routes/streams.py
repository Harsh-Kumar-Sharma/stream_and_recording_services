from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.exceptions import MediaServiceError
from app.middleware.auth_middleware import error_response
from app.services.stream_service import StreamService

router = APIRouter(prefix="/api/v1/streams", tags=["streams"])


def get_stream_service(request: Request) -> StreamService:
    service = getattr(request.app.state, "stream_service", None)
    if service is None:
        service = StreamService(get_settings())
        request.app.state.stream_service = service
    return service


@router.post("/{camera_id}/start")
async def start_stream(camera_id: str, request: Request) -> dict:
    try:
        state = await get_stream_service(request).start_stream(camera_id, request.state.bearer_token)
        return state.to_response()
    except MediaServiceError as exc:
        return error_response(exc.status_code, exc.message, exc.error_code)


@router.post("/{camera_id}/stop")
async def stop_stream(camera_id: str, request: Request) -> dict:
    return await get_stream_service(request).stop_stream(camera_id)


@router.get("/{camera_id}/status")
async def stream_status(camera_id: str, request: Request) -> dict:
    return await get_stream_service(request).get_status(camera_id)


@router.get("")
async def list_streams(request: Request) -> dict:
    return await get_stream_service(request).list_streams()

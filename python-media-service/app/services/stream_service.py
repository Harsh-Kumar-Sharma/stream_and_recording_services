import asyncio

from app.core.config import Settings
from app.core.exceptions import MediaServiceError
from app.schemas.stream import StreamState
from app.services.camera_service import CameraService
from app.services.mediamtx_service import MediaMtxService


class StreamService:
    def __init__(
        self,
        settings: Settings,
        camera_service: CameraService | None = None,
        mediamtx_service: MediaMtxService | None = None,
    ) -> None:
        self.settings = settings
        self.camera_service = camera_service or CameraService(settings)
        self.mediamtx_service = mediamtx_service or MediaMtxService(settings)
        self._streams: dict[str, StreamState] = {}
        self._lock = asyncio.Lock()

    async def start_stream(self, camera_id: str, bearer_token: str) -> StreamState:
        async with self._lock:
            existing = self._streams.get(camera_id)
            if existing and existing.stream_status == "started":
                return existing

            if len(self._streams) >= self.settings.worker.max_live_streams:
                raise MediaServiceError("Maximum live stream limit reached", "MAX_LIVE_STREAMS_REACHED", 429)

            camera = await self.camera_service.get_active_camera(camera_id, bearer_token)
            path = await self.mediamtx_service.ensure_stream_path(camera)
            stream_url = self.mediamtx_service.hls_url_for_path(path)
            state = StreamState(
                camera_id=camera.camera_id,
                camera_name=camera.camera_name,
                stream_status="started",
                stream_url=stream_url,
                path=path,
            )
            self._streams[camera_id] = state
            return state

    async def stop_stream(self, camera_id: str) -> dict:
        async with self._lock:
            existing = self._streams.pop(camera_id, None)
            return {
                "status": True,
                "cameraId": camera_id,
                "streamStatus": "stopped" if existing else "inactive",
            }

    async def get_status(self, camera_id: str) -> dict:
        state = self._streams.get(camera_id)
        if not state:
            return {
                "status": True,
                "cameraId": camera_id,
                "streamStatus": "inactive",
                "streamType": "hls",
                "streamUrl": None,
                "lastError": None,
            }
        return state.to_response()

    async def list_streams(self) -> dict:
        return {
            "status": True,
            "streams": [state.to_response() for state in self._streams.values()],
            "count": len(self._streams),
        }

    def active_count(self) -> int:
        return len(self._streams)

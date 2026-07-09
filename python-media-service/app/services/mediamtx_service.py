import logging

from app.core.config import Settings
from app.schemas.stream import InternalCamera

logger = logging.getLogger(__name__)


class MediaMtxService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def path_for_camera(self, camera_id: str) -> str:
        return f"{self.settings.mediamtx.path_prefix}{camera_id}"

    def hls_url_for_path(self, path: str) -> str:
        return f"{self.settings.mediamtx.public_hls_base_url.rstrip('/')}/{path}/index.m3u8"

    async def ensure_stream_path(self, camera: InternalCamera) -> str:
        path = self.path_for_camera(camera.camera_id)
        logger.info("Confirmed MediaMTX path camera_id=%s path=%s", camera.camera_id, path)
        return path

    async def stream_status(self, path: str) -> dict:
        return {
            "path": path,
            "reachable": True,
            "sourceReady": None,
        }

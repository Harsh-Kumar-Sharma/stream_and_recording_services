import logging

from app.core.config import Settings
from app.core.exceptions import CameraInactiveError
from app.core.logging import mask_rtsp_url
from app.schemas.stream import InternalCamera
from app.services.java_client import JavaApiClient

logger = logging.getLogger(__name__)


class CameraService:
    def __init__(self, settings: Settings, java_client: JavaApiClient | None = None) -> None:
        self.settings = settings
        self.java_client = java_client or JavaApiClient(settings)

    async def get_active_camera(self, camera_id: str, bearer_token: str) -> InternalCamera:
        camera = await self.java_client.get_camera_device_info(camera_id, bearer_token)
        logger.info("Fetched camera device info camera_id=%s rtsp=%s", camera.camera_id, mask_rtsp_url(camera.rtsp_url))

        if camera.status.lower() != "active":
            raise CameraInactiveError(f"Camera {camera.camera_id} is inactive")

        return InternalCamera(
            camera_id=camera.camera_id,
            camera_name=camera.camera_name,
            rtsp_url=camera.rtsp_url,
            ip_address=camera.ip_address,
            status=camera.status,
            site_id=camera.site_id,
            gantry_id=camera.gantry_id,
            lane_id=camera.lane_id,
        )

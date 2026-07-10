import logging
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.core.exceptions import MediaMtxError
from app.core.logging import mask_rtsp_url
from app.schemas.stream import InternalCamera

logger = logging.getLogger(__name__)


class MediaMtxService:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport
        self.base_url = settings.mediamtx.base_url.rstrip("/")

    def path_for_camera(self, camera_id: str) -> str:
        return f"{self.settings.mediamtx.path_prefix}{camera_id}"

    def hls_url_for_path(self, path: str) -> str:
        return f"{self.settings.mediamtx.public_hls_base_url.rstrip('/')}/{path}/index.m3u8"

    def webrtc_url_for_path(self, path: str) -> str:
        return f"{self.settings.mediamtx.public_webrtc_base_url.rstrip('/')}/{path}/"

    def webrtc_whep_url_for_path(self, path: str) -> str:
        return f"{self.settings.mediamtx.public_webrtc_base_url.rstrip('/')}/{path}/whep"

    async def ensure_stream_path(self, camera: InternalCamera) -> str:
        path = self.path_for_camera(camera.camera_id)
        if self.settings.mediamtx.auto_create_paths:
            await self._upsert_rtsp_source_path(path, camera)
        logger.info("Confirmed MediaMTX path camera_id=%s path=%s", camera.camera_id, path)
        return path

    async def stream_status(self, path: str) -> dict:
        return {
            "path": path,
            "reachable": True,
            "sourceReady": None,
        }

    async def _upsert_rtsp_source_path(self, path: str, camera: InternalCamera) -> None:
        path_name = quote(path, safe="")
        payload = {
            "source": camera.rtsp_url,
            "sourceProtocol": self.settings.mediamtx.rtsp_transport,
        }

        try:
            async with httpx.AsyncClient(timeout=5, transport=self.transport, trust_env=False) as client:
                patch_response = await client.patch(f"{self.base_url}/v3/config/paths/patch/{path_name}", json=payload)
                if patch_response.status_code == 404:
                    add_response = await client.post(f"{self.base_url}/v3/config/paths/add/{path_name}", json=payload)
                    self._raise_for_api_error(add_response, path, camera)
                    logger.info(
                        "Added MediaMTX RTSP source path camera_id=%s path=%s source=%s",
                        camera.camera_id,
                        path,
                        mask_rtsp_url(camera.rtsp_url),
                    )
                    return

                self._raise_for_api_error(patch_response, path, camera)
                logger.info(
                    "Updated MediaMTX RTSP source path camera_id=%s path=%s source=%s",
                    camera.camera_id,
                    path,
                    mask_rtsp_url(camera.rtsp_url),
                )
        except httpx.TransportError as exc:
            logger.error(
                "MediaMTX API is unreachable base_url=%s camera_id=%s path=%s error=%s",
                self.base_url,
                camera.camera_id,
                path,
                exc,
            )
            raise MediaMtxError(f"MediaMTX API is unreachable at {self.base_url}") from exc

    def _raise_for_api_error(self, response: httpx.Response, path: str, camera: InternalCamera) -> None:
        if response.status_code < 400:
            return

        logger.error(
            "MediaMTX path setup failed camera_id=%s path=%s status_code=%s response=%s",
            camera.camera_id,
            path,
            response.status_code,
            response.text,
        )
        raise MediaMtxError(f"MediaMTX path setup failed for {camera.camera_id}")

import asyncio
import unittest
from pathlib import Path

from app.core.config import load_settings
from app.schemas.stream import InternalCamera
from app.services.stream_service import StreamService


class StubCameraService:
    async def get_active_camera(self, camera_id: str, bearer_token: str) -> InternalCamera:
        return InternalCamera(
            camera_id=camera_id,
            camera_name="Gantry Camera",
            rtsp_url="rtsp://user:secret@192.168.1.10:554/stream1",
            ip_address="192.168.1.10",
            status="active",
        )


class StubMediaMtxService:
    async def ensure_stream_path(self, camera: InternalCamera) -> str:
        return f"cam-{camera.camera_id}"

    def hls_url_for_path(self, path: str) -> str:
        return f"http://localhost:8888/{path}/index.m3u8"

    def webrtc_url_for_path(self, path: str) -> str:
        return f"http://localhost:8889/{path}/"

    def webrtc_whep_url_for_path(self, path: str) -> str:
        return f"http://localhost:8889/{path}/whep"


def settings_for_test():
    return load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")


class StreamServiceTests(unittest.TestCase):
    def test_start_stream_returns_hls_url_without_rtsp(self) -> None:
        service = StreamService(
            settings_for_test(),
            camera_service=StubCameraService(),
            mediamtx_service=StubMediaMtxService(),
        )

        state = asyncio.run(service.start_stream("CAM-101", "token"))
        response = state.to_response()

        self.assertEqual(response["streamStatus"], "started")
        self.assertEqual(response["streamUrl"], "http://localhost:8888/cam-CAM-101/index.m3u8")
        self.assertEqual(response["webrtcUrl"], "http://localhost:8889/cam-CAM-101/")
        self.assertEqual(response["webrtcWhepUrl"], "http://localhost:8889/cam-CAM-101/whep")
        self.assertNotIn("rtsp", str(response).lower())

    def test_stop_stream_returns_success(self) -> None:
        service = StreamService(
            settings_for_test(),
            camera_service=StubCameraService(),
            mediamtx_service=StubMediaMtxService(),
        )
        asyncio.run(service.start_stream("CAM-101", "token"))

        response = asyncio.run(service.stop_stream("CAM-101"))

        self.assertEqual(response["streamStatus"], "stopped")
        self.assertEqual(service.active_count(), 0)

    def test_status_returns_inactive_when_missing(self) -> None:
        service = StreamService(
            settings_for_test(),
            camera_service=StubCameraService(),
            mediamtx_service=StubMediaMtxService(),
        )

        response = asyncio.run(service.get_status("CAM-404"))

        self.assertEqual(response["streamStatus"], "inactive")


if __name__ == "__main__":
    unittest.main()

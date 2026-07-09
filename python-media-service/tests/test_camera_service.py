import asyncio
import unittest
from pathlib import Path

from app.core.config import load_settings
from app.core.exceptions import CameraInactiveError
from app.schemas.camera import CameraDeviceInfo
from app.services.camera_service import CameraService


class StubJavaClient:
    def __init__(self, status: str = "active") -> None:
        self.status = status

    async def get_camera_device_info(self, camera_id: str, token: str) -> CameraDeviceInfo:
        return CameraDeviceInfo.model_validate(
            {
                "cameraId": camera_id,
                "cameraName": "Gantry Camera",
                "rtspUrl": "rtsp://user:secret@192.168.1.10:554/stream1",
                "ipAddress": "192.168.1.10",
                "status": self.status,
                "siteId": "SITE-01",
                "gantryId": "GANTRY-01",
                "laneId": "LANE-01",
            }
        )


def settings_for_test():
    return load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")


class CameraServiceTests(unittest.TestCase):
    def test_get_active_camera_returns_internal_camera(self) -> None:
        service = CameraService(settings_for_test(), java_client=StubJavaClient())

        camera = asyncio.run(service.get_active_camera("CAM-101", "token"))

        self.assertEqual(camera.camera_id, "CAM-101")
        self.assertEqual(camera.rtsp_url, "rtsp://user:secret@192.168.1.10:554/stream1")

    def test_inactive_camera_raises_error(self) -> None:
        service = CameraService(settings_for_test(), java_client=StubJavaClient("inactive"))

        with self.assertRaises(CameraInactiveError):
            asyncio.run(service.get_active_camera("CAM-101", "token"))


if __name__ == "__main__":
    unittest.main()

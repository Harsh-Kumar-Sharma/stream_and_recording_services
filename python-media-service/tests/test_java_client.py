import asyncio
import unittest
from pathlib import Path

import httpx

from app.core.config import load_settings
from app.core.exceptions import CameraNotFoundError
from app.services.java_client import JavaApiClient


def settings_for_test():
    settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    settings.java_api.retry_count = 0
    return settings


class JavaApiClientTests(unittest.TestCase):
    def test_validate_token_returns_dev_bypass_session_without_api_call(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.fail("validate_token should not call Java while dev bypass is enabled")

        client = JavaApiClient(settings_for_test(), transport=httpx.MockTransport(handler))
        session = asyncio.run(client.validate_token("any-token"))

        self.assertTrue(session.valid)
        self.assertEqual(session.user_id, "DEV-BYPASS-USER")
        self.assertEqual(session.roles, ["ADMIN"])
        self.assertIn("CAMERA_LIVE_VIEW", session.permissions)

    def test_camera_device_info_response_is_parsed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "cameraId": "CAM-101",
                    "cameraName": "Gantry 1 Lane 1 Camera",
                    "rtspUrl": "rtsp://user:secret@192.168.1.10:554/stream1",
                    "ipAddress": "192.168.1.10",
                    "status": "active",
                    "siteId": "SITE-01",
                    "gantryId": "GANTRY-01",
                    "laneId": "LANE-01",
                },
            )

        client = JavaApiClient(settings_for_test(), transport=httpx.MockTransport(handler))
        camera = asyncio.run(client.get_camera_device_info("CAM-101", "valid-token"))

        self.assertEqual(camera.camera_id, "CAM-101")
        self.assertEqual(camera.status, "active")

    def test_stream_devices_list_response_is_matched_by_custom_device_id(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/api/devices/stream/all")
            return httpx.Response(
                200,
                json=[
                    {
                        "deviceId": 2,
                        "customDeviceId": "CAM-02\n",
                        "ipAddress": "192.168.38\n",
                        "username": "User1",
                        "password": "PassWd",
                        "portNumber": 765,
                        "rtspUrl": "rtsp://192.168.2",
                    },
                    {
                        "deviceId": 6,
                        "customDeviceId": "CAM-06\n",
                        "ipAddress": "192.168.32\n",
                        "username": "User1",
                        "password": "PassWd",
                        "portNumber": 765,
                        "rtspUrl": "rtsp://192.168.6",
                    },
                ],
            )

        client = JavaApiClient(settings_for_test(), transport=httpx.MockTransport(handler))
        camera = asyncio.run(client.get_camera_device_info("CAM-02", "valid-token"))

        self.assertEqual(camera.camera_id, "CAM-02")
        self.assertEqual(camera.camera_name, "CAM-02")
        self.assertEqual(camera.ip_address, "192.168.38")
        self.assertEqual(camera.rtsp_url, "rtsp://192.168.2")
        self.assertEqual(camera.status, "active")
        self.assertEqual(camera.device_id, 2)

    def test_stream_devices_list_response_is_matched_by_device_id(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {
                        "deviceId": 6,
                        "customDeviceId": "CAM-06\n",
                        "ipAddress": "192.168.32\n",
                        "username": "User1",
                        "password": "PassWd",
                        "portNumber": 765,
                        "rtspUrl": "rtsp://192.168.6",
                    },
                ],
            )

        client = JavaApiClient(settings_for_test(), transport=httpx.MockTransport(handler))
        camera = asyncio.run(client.get_camera_device_info("6", "valid-token"))

        self.assertEqual(camera.camera_id, "CAM-06")
        self.assertEqual(camera.device_id, 6)

    def test_stream_devices_list_missing_camera_raises_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        client = JavaApiClient(settings_for_test(), transport=httpx.MockTransport(handler))

        with self.assertRaises(CameraNotFoundError):
            asyncio.run(client.get_camera_device_info("CAM-404", "valid-token"))


if __name__ == "__main__":
    unittest.main()

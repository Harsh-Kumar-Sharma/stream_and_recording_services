import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from app.core.config import load_settings
from app.core.exceptions import MediaMtxError
from app.schemas.stream import InternalCamera
from app.services.mediamtx_service import MediaMtxService


class MediaMtxServiceTests(unittest.TestCase):
    def test_path_and_hls_url_use_config(self) -> None:
        with patch.dict(
            "os.environ",
            {"MEDIA_SERVICE__MEDIAMTX__PUBLIC_HLS_BASE_URL": "http://localhost:8888"},
        ):
            settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
        service = MediaMtxService(settings)

        path = service.path_for_camera("CAM-101")
        url = service.hls_url_for_path(path)
        webrtc_url = service.webrtc_url_for_path(path)
        webrtc_whep_url = service.webrtc_whep_url_for_path(path)

        self.assertEqual(path, "cam-CAM-101")
        self.assertEqual(url, "http://localhost:8888/cam-CAM-101/index.m3u8")
        self.assertEqual(webrtc_url, "http://192.168.0.103:8889/cam-CAM-101/")
        self.assertEqual(webrtc_whep_url, "http://192.168.0.103:8889/cam-CAM-101/whep")

    def test_ensure_stream_path_patches_existing_mediamtx_path(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json={"status": "ok"})

        service = MediaMtxService(settings_for_test(), transport=httpx.MockTransport(handler))

        path = asyncio.run(service.ensure_stream_path(camera_for_test()))

        self.assertEqual(path, "cam-CAM-101")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].method, "PATCH")
        self.assertEqual(requests[0].url.path, "/v3/config/paths/patch/cam-CAM-101")
        self.assertIn("rtsp://user:secret@192.168.1.10:554/stream1", requests[0].content.decode())

    def test_ensure_stream_path_adds_missing_mediamtx_path(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.method == "PATCH":
                return httpx.Response(404, json={"error": "not found"})
            return httpx.Response(200, json={"status": "ok"})

        service = MediaMtxService(settings_for_test(), transport=httpx.MockTransport(handler))

        path = asyncio.run(service.ensure_stream_path(camera_for_test()))

        self.assertEqual(path, "cam-CAM-101")
        self.assertEqual([request.method for request in requests], ["PATCH", "POST"])
        self.assertEqual(requests[1].url.path, "/v3/config/paths/add/cam-CAM-101")

    def test_ensure_stream_path_maps_connection_failure_to_mediamtx_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("All connection attempts failed")

        service = MediaMtxService(settings_for_test(), transport=httpx.MockTransport(handler))

        with self.assertRaises(MediaMtxError) as ctx:
            asyncio.run(service.ensure_stream_path(camera_for_test()))

        self.assertIn("MediaMTX API is unreachable", ctx.exception.message)


def settings_for_test():
    return load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")


def camera_for_test() -> InternalCamera:
    return InternalCamera(
        camera_id="CAM-101",
        camera_name="Gantry Camera",
        rtsp_url="rtsp://user:secret@192.168.1.10:554/stream1",
        ip_address="192.168.1.10",
        status="active",
    )


if __name__ == "__main__":
    unittest.main()

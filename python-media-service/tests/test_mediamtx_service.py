import unittest
from pathlib import Path

from app.core.config import load_settings
from app.services.mediamtx_service import MediaMtxService


class MediaMtxServiceTests(unittest.TestCase):
    def test_path_and_hls_url_use_config(self) -> None:
        settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
        service = MediaMtxService(settings)

        path = service.path_for_camera("CAM-101")
        url = service.hls_url_for_path(path)

        self.assertEqual(path, "cam-CAM-101")
        self.assertEqual(url, "https://media.example.com/cam-CAM-101/index.m3u8")


if __name__ == "__main__":
    unittest.main()

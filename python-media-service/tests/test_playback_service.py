import base64
import unittest
from pathlib import Path

from app.core.config import load_settings
from app.core.exceptions import InvalidFilePathError
from app.services.playback_service import PlaybackService


TEST_STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage" / "test-playback"


def case_storage(name: str) -> Path:
    root = TEST_STORAGE_ROOT / name
    root.mkdir(parents=True, exist_ok=True)
    return root


def settings_for_test(storage_root: Path):
    settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    settings.recording.storage_root = storage_root
    return settings


class PlaybackServiceTests(unittest.TestCase):
    def test_search_returns_matching_camera_files_with_safe_urls(self) -> None:
        storage_root = case_storage("search")
        target_dir = storage_root / "CAM-101" / "2026-07-09" / "10"
        other_dir = storage_root / "CAM-102" / "2026-07-09" / "10"
        target_dir.mkdir(parents=True, exist_ok=True)
        other_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "CAM-101_20260709_100000.mp4").write_bytes(b"video")
        (other_dir / "CAM-102_20260709_100000.mp4").write_bytes(b"other")

        service = PlaybackService(settings_for_test(storage_root))
        response = service.search("CAM-101")

        self.assertEqual(len(response["files"]), 1)
        self.assertEqual(response["files"][0]["fileName"], "CAM-101_20260709_100000.mp4")
        self.assertIn("/api/v1/playback/CAM-101/file?path=", response["files"][0]["playbackUrl"])
        self.assertNotIn(str(storage_root), response["files"][0]["playbackUrl"])

    def test_list_files_filters_by_date(self) -> None:
        storage_root = case_storage("list")
        target_dir = storage_root / "CAM-101" / "2026-07-09" / "10"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "CAM-101_20260709_100000.mp4").write_bytes(b"video")

        service = PlaybackService(settings_for_test(storage_root))
        response = service.list_files("CAM-101", "2026-07-09")

        self.assertEqual(len(response["files"]), 1)

    def test_resolve_file_token_blocks_path_traversal(self) -> None:
        service = PlaybackService(settings_for_test(case_storage("traversal")))
        token = base64.urlsafe_b64encode(b"../secret.mp4").decode("ascii")

        with self.assertRaises(InvalidFilePathError):
            service.resolve_file_token("CAM-101", token)

    def test_resolve_file_token_returns_storage_file(self) -> None:
        storage_root = case_storage("resolve")
        target_dir = storage_root / "CAM-101" / "2026-07-09" / "10"
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "CAM-101_20260709_100000.mp4"
        file_path.write_bytes(b"video")

        service = PlaybackService(settings_for_test(storage_root))
        token = service.list_files("CAM-101")["files"][0]["token"]
        resolved = service.resolve_file_token("CAM-101", token)

        self.assertEqual(resolved, file_path.resolve())


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import load_settings
from app.core.exceptions import StorageNotAvailableError
from app.services.storage_service import StorageService


TEST_STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage" / "test-storage"


def settings_for_test(name: str):
    settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    settings.recording.storage_root = TEST_STORAGE_ROOT / name
    settings.storage.retention_days = 1
    settings.storage.cleanup_enabled = True
    return settings


class StorageServiceTests(unittest.TestCase):
    def test_ensure_storage_ready_creates_writable_root(self) -> None:
        service = StorageService(settings_for_test("ready"))

        service.ensure_storage_ready()

        self.assertTrue(service.storage_root.exists())
        self.assertGreaterEqual(service.free_disk_percent(), 0)

    def test_ensure_storage_ready_blocks_low_disk_threshold(self) -> None:
        settings = settings_for_test("low-disk")
        settings.storage.min_free_disk_percent = 101
        service = StorageService(settings)

        with self.assertRaises(StorageNotAvailableError):
            service.ensure_storage_ready()

    def test_cleanup_old_files_deletes_expired_mp4(self) -> None:
        service = StorageService(settings_for_test("cleanup"))
        target_dir = service.storage_root / "CAM-101" / "2026-07-09" / "10"
        target_dir.mkdir(parents=True, exist_ok=True)
        old_file = target_dir / "old.mp4"
        new_file = target_dir / "new.mp4"
        old_file.write_bytes(b"old")
        new_file.write_bytes(b"new")
        old_time = (datetime.now() - timedelta(days=3)).timestamp()
        os.utime(old_file, (old_time, old_time))

        result = service.cleanup_old_files()

        self.assertEqual(result["deletedFiles"], 1)
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())


if __name__ == "__main__":
    unittest.main()

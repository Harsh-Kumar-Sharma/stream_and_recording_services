import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import StorageNotAvailableError

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage_root = Path(settings.recording.storage_root).resolve()

    def ensure_storage_ready(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        probe = self.storage_root / ".write-check"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except OSError as exc:
            logger.error("Recording storage is not writable path=%s error=%s", self.storage_root, exc)
            raise StorageNotAvailableError("Recording storage is not writable") from exc

        if self.free_disk_percent() < self.settings.storage.min_free_disk_percent:
            logger.error("Recording storage free space is below threshold path=%s free_percent=%s threshold=%s", self.storage_root, self.free_disk_percent(), self.settings.storage.min_free_disk_percent)
            raise StorageNotAvailableError("Recording storage free space is below configured threshold")

    def free_disk_percent(self) -> float:
        usage = shutil.disk_usage(self.storage_root)
        if usage.total == 0:
            return 0.0
        return round((usage.free / usage.total) * 100, 2)

    def cleanup_old_files(self, now: datetime | None = None) -> dict:
        if not self.settings.storage.cleanup_enabled:
            return {"status": True, "deletedFiles": 0, "enabled": False}

        self.storage_root.mkdir(parents=True, exist_ok=True)
        cutoff = (now or datetime.now()) - timedelta(days=self.settings.storage.retention_days)
        deleted = 0
        for path in self.storage_root.rglob(f"*.{self.settings.recording.file_extension}"):
            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
            if modified_at < cutoff:
                path.unlink()
                deleted += 1

        return {"status": True, "deletedFiles": deleted, "enabled": True}

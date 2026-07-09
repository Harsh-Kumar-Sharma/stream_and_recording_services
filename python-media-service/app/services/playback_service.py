import base64
from datetime import datetime
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import InvalidFilePathError, PlaybackFileNotFoundError
from app.schemas.playback import PlaybackFile


class PlaybackService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage_root = Path(settings.recording.storage_root).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def search(self, camera_id: str, from_time: datetime | None = None, to_time: datetime | None = None) -> dict:
        files = self._find_files(camera_id, from_time, to_time)
        return {
            "status": True,
            "cameraId": camera_id,
            "files": [file.to_response() for file in files],
        }

    def list_files(self, camera_id: str, date: str | None = None) -> dict:
        camera_root = self._safe_camera_root(camera_id)
        search_root = camera_root / date if date else camera_root
        files = []
        if search_root.exists():
            for path in sorted(search_root.rglob(f"*.{self.settings.recording.file_extension}")):
                files.append(self._to_playback_file(camera_id, path))

        return {
            "status": True,
            "cameraId": camera_id,
            "files": [file.to_response() for file in files],
        }

    def resolve_file_token(self, camera_id: str, token: str) -> Path:
        try:
            relative_text = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        except Exception as exc:
            raise InvalidFilePathError() from exc

        relative_path = Path(relative_text)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise InvalidFilePathError()

        resolved = (self.storage_root / relative_path).resolve()
        if not self._is_under_storage_root(resolved):
            raise InvalidFilePathError()
        if not resolved.exists() or not resolved.is_file():
            raise PlaybackFileNotFoundError()
        if resolved.suffix.lower() != f".{self.settings.recording.file_extension.lower()}":
            raise InvalidFilePathError()
        if not resolved.relative_to(self.storage_root).parts[0] == camera_id:
            raise InvalidFilePathError()
        return resolved

    def _find_files(self, camera_id: str, from_time: datetime | None, to_time: datetime | None) -> list[PlaybackFile]:
        camera_root = self._safe_camera_root(camera_id)
        if not camera_root.exists():
            return []

        files = []
        for path in sorted(camera_root.rglob(f"*.{self.settings.recording.file_extension}")):
            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
            if from_time and modified_at < from_time:
                continue
            if to_time and modified_at > to_time:
                continue
            files.append(self._to_playback_file(camera_id, path, modified_at))
        return files

    def _safe_camera_root(self, camera_id: str) -> Path:
        if "/" in camera_id or "\\" in camera_id or ".." in camera_id:
            raise InvalidFilePathError()
        camera_root = (self.storage_root / camera_id).resolve()
        if not self._is_under_storage_root(camera_root):
            raise InvalidFilePathError()
        return camera_root

    def _to_playback_file(self, camera_id: str, path: Path, modified_at: datetime | None = None) -> PlaybackFile:
        resolved = path.resolve()
        if not self._is_under_storage_root(resolved):
            raise InvalidFilePathError()
        relative_path = resolved.relative_to(self.storage_root)
        token = base64.urlsafe_b64encode(str(relative_path).encode("utf-8")).decode("ascii")
        return PlaybackFile(
            file_name=resolved.name,
            camera_id=camera_id,
            size_bytes=resolved.stat().st_size,
            modified_at=modified_at or datetime.fromtimestamp(resolved.stat().st_mtime),
            playback_url=f"/api/v1/playback/{camera_id}/file?path={token}",
            token=token,
        )

    def _is_under_storage_root(self, path: Path) -> bool:
        try:
            path.relative_to(self.storage_root)
            return True
        except ValueError:
            return False

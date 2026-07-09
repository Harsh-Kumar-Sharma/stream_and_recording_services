from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RecordingState(BaseModel):
    camera_id: str
    camera_name: str
    pid: int | None
    recording_status: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stopped_at: datetime | None = None
    restart_count: int = 0
    latest_output_file: str | None = None
    storage_path: str
    last_error: str | None = None

    def to_response(self) -> dict:
        return {
            "status": True,
            "cameraId": self.camera_id,
            "cameraName": self.camera_name,
            "pid": self.pid,
            "recordingStatus": self.recording_status,
            "startedAt": self.started_at.isoformat(),
            "stoppedAt": self.stopped_at.isoformat() if self.stopped_at else None,
            "restartCount": self.restart_count,
            "latestOutputFile": self.latest_output_file,
            "storagePath": self.storage_path,
            "lastError": self.last_error,
        }

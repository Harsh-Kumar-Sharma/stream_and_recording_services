from datetime import datetime, timezone

from pydantic import BaseModel, Field


class InternalCamera(BaseModel):
    camera_id: str
    camera_name: str
    rtsp_url: str
    ip_address: str
    status: str
    site_id: str | None = None
    gantry_id: str | None = None
    lane_id: str | None = None


class StreamState(BaseModel):
    camera_id: str
    camera_name: str
    stream_status: str
    stream_type: str = "hls"
    stream_url: str
    path: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_error: str | None = None

    def to_response(self) -> dict:
        return {
            "status": True,
            "cameraId": self.camera_id,
            "cameraName": self.camera_name,
            "streamStatus": self.stream_status,
            "streamType": self.stream_type,
            "streamUrl": self.stream_url,
            "startedAt": self.started_at.isoformat(),
            "lastError": self.last_error,
        }

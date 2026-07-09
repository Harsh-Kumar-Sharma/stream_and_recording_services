from datetime import datetime

from pydantic import BaseModel


class PlaybackFile(BaseModel):
    file_name: str
    camera_id: str
    size_bytes: int
    modified_at: datetime
    playback_url: str
    token: str

    def to_response(self) -> dict:
        return {
            "fileName": self.file_name,
            "cameraId": self.camera_id,
            "sizeBytes": self.size_bytes,
            "modifiedAt": self.modified_at.isoformat(),
            "playbackUrl": self.playback_url,
            "token": self.token,
        }

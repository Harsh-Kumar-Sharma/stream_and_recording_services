from datetime import datetime
from pathlib import Path

from app.core.config import Settings
from app.schemas.stream import InternalCamera


def recording_output_dir(settings: Settings, camera_id: str, now: datetime | None = None) -> Path:
    current = now or datetime.now()
    return Path(settings.recording.storage_root) / camera_id / current.strftime("%Y-%m-%d") / current.strftime("%H")


def recording_output_pattern(settings: Settings, camera_id: str, now: datetime | None = None) -> Path:
    output_dir = recording_output_dir(settings, camera_id, now)
    return output_dir / f"{camera_id}_%Y%m%d_%H%M%S.{settings.recording.file_extension}"


def build_ffmpeg_command(settings: Settings, camera: InternalCamera, now: datetime | None = None) -> list[str]:
    output_dir = recording_output_dir(settings, camera.camera_id, now)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = recording_output_pattern(settings, camera.camera_id, now)

    command = [
        settings.recording.ffmpeg_path,
        "-rtsp_transport",
        settings.recording.rtsp_transport,
        "-i",
        camera.rtsp_url,
        "-map",
        "0:v:0",
    ]

    if not settings.recording.include_audio:
        command.append("-an")

    command.extend(
        [
            "-c:v",
            settings.recording.video_codec_mode,
            "-f",
            "segment",
            "-segment_time",
            str(settings.recording.segment_duration_seconds),
            "-reset_timestamps",
            "1",
            "-strftime",
            "1",
            str(output_pattern),
        ]
    )
    return command

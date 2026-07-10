import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class AppConfig(BaseModel):
    name: str
    environment: str
    host: str
    port: int
    log_level: str = "INFO"


class JavaApiConfig(BaseModel):
    base_url: str
    session_validate_endpoint: str
    camera_stream_all_endpoint: str = "/api/devices/stream/all"
    timeout_seconds: float
    retry_count: int = Field(ge=0)


class SecurityConfig(BaseModel):
    enable_bearer_validation: bool
    mask_rtsp_url_in_logs: bool
    allow_docs_in_production: bool
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True


class MediaMtxConfig(BaseModel):
    base_url: str
    public_hls_base_url: str
    public_webrtc_base_url: str
    rtsp_transport: str = "tcp"
    path_prefix: str = "cam-"
    auto_create_paths: bool = True
    start_on_demand: bool = True


class RecordingConfig(BaseModel):
    enabled: bool
    storage_root: Path
    segment_duration_seconds: int = Field(gt=0)
    file_extension: str = "mp4"
    ffmpeg_path: str
    rtsp_transport: str = "tcp"
    video_codec_mode: str = "copy"
    include_audio: bool = False
    max_restart_attempts: int = Field(ge=0)
    restart_delay_seconds: int = Field(ge=0)
    stop_grace_seconds: int = Field(gt=0)


class WorkerConfig(BaseModel):
    max_recording_workers: int = Field(gt=0)
    max_live_streams: int = Field(gt=0)
    health_check_interval_seconds: int = Field(gt=0)
    inactive_stream_ttl_seconds: int = Field(gt=0)


class StorageConfig(BaseModel):
    retention_days: int = Field(gt=0)
    min_free_disk_percent: int = Field(ge=0, le=100)
    cleanup_enabled: bool


class DatabaseConfig(BaseModel):
    enabled: bool = False
    type: str
    host: str = ""
    port: int
    name: str = ""
    username: str = ""
    password: str = ""


class Settings(BaseModel):
    app: AppConfig
    java_api: JavaApiConfig
    security: SecurityConfig
    mediamtx: MediaMtxConfig
    recording: RecordingConfig
    worker: WorkerConfig
    storage: StorageConfig
    database: DatabaseConfig


class ConfigError(RuntimeError):
    pass


def _parse_env_value(value: str) -> Any:
    try:
        return yaml.safe_load(value)
    except yaml.YAMLError:
        return value


def _deep_set(config: dict[str, Any], dotted_key: str, value: str) -> None:
    keys = dotted_key.lower().split("__")
    current = config
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = _parse_env_value(value)


def _apply_env_overrides(config: dict[str, Any]) -> None:
    prefix = "MEDIA_SERVICE__"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            _deep_set(config, key.removeprefix(prefix), value)


def load_settings(config_path: str | Path | None = None) -> Settings:
    path = Path(config_path or os.getenv("MEDIA_SERVICE_CONFIG", DEFAULT_CONFIG_PATH))
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Config file is not valid YAML: {path}") from exc

    if not isinstance(loaded, dict):
        raise ConfigError(f"Config file must contain a YAML object: {path}")

    _apply_env_overrides(loaded)

    try:
        return Settings.model_validate(loaded)
    except ValidationError as exc:
        raise ConfigError(f"Config validation failed: {exc}") from exc


@lru_cache
def get_settings() -> Settings:
    return load_settings()

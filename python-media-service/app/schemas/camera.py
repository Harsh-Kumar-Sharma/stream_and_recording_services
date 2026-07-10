from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class CameraDeviceInfo(BaseModel):
    camera_id: str = Field(alias="cameraId")
    camera_name: str = Field(alias="cameraName")
    rtsp_url: str = Field(alias="rtspUrl")
    ip_address: str = Field(alias="ipAddress")
    status: str
    site_id: str | None = Field(default=None, alias="siteId")
    gantry_id: str | None = Field(default=None, alias="gantryId")
    lane_id: str | None = Field(default=None, alias="laneId")
    device_id: int | None = Field(default=None, alias="deviceId")
    username: str | None = None
    password: str | None = None
    port_number: int | None = Field(default=None, alias="portNumber")

    @model_validator(mode="before")
    @classmethod
    def normalize_java_stream_device(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = {key: value.strip() if isinstance(value, str) else value for key, value in data.items()}

        if "customDeviceId" in normalized and "cameraId" not in normalized:
            normalized["cameraId"] = normalized["customDeviceId"]
        if "cameraName" not in normalized:
            normalized["cameraName"] = normalized.get("customDeviceId") or f"Device {normalized.get('deviceId')}"
        if "status" not in normalized:
            normalized["status"] = "active"

        return normalized

    @field_validator("camera_id", "camera_name", "rtsp_url", "ip_address", "status", mode="before")
    @classmethod
    def trim_required_strings(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

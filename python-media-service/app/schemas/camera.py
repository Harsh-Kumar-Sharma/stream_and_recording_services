from pydantic import BaseModel, Field


class CameraDeviceInfo(BaseModel):
    camera_id: str = Field(alias="cameraId")
    camera_name: str = Field(alias="cameraName")
    rtsp_url: str = Field(alias="rtspUrl")
    ip_address: str = Field(alias="ipAddress")
    status: str
    site_id: str | None = Field(default=None, alias="siteId")
    gantry_id: str | None = Field(default=None, alias="gantryId")
    lane_id: str | None = Field(default=None, alias="laneId")

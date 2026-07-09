from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

app = FastAPI(title="mock-java-api")


def _is_valid_token(authorization: str | None) -> bool:
    return authorization == "Bearer mock-valid-token"


@app.get("/api/auth/session/validate")
async def validate_session(authorization: str | None = Header(default=None)):
    if not _is_valid_token(authorization):
        return JSONResponse(status_code=401, content={"valid": False, "message": "Invalid or expired token"})

    return {
        "valid": True,
        "userId": "USER-101",
        "username": "mock-operator",
        "roles": ["ADMIN"],
        "permissions": ["CAMERA_LIVE_VIEW", "CAMERA_PLAYBACK", "CAMERA_RECORDING"],
    }


@app.get("/api/cameras/{camera_id}/device-info")
async def camera_device_info(camera_id: str, authorization: str | None = Header(default=None)):
    if not _is_valid_token(authorization):
        return JSONResponse(status_code=401, content={"status": False, "message": "Invalid or expired token"})

    return {
        "cameraId": camera_id,
        "cameraName": "Mock MediaMTX Test Camera",
        "rtspUrl": f"rtsp://mediamtx:8554/cam-{camera_id}",
        "ipAddress": "mediamtx",
        "status": "active",
        "siteId": "SITE-MOCK",
        "gantryId": "GANTRY-MOCK",
        "laneId": "LANE-MOCK",
    }

import unittest
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes.recorders import router


class RequestStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.bearer_token = "token"
        return await call_next(request)


class StubRecordingState:
    def to_response(self) -> dict:
        return {
            "status": True,
            "cameraId": "CAM-101",
            "cameraName": "Gantry Camera",
            "pid": 12345,
            "recordingStatus": "recording",
            "startedAt": "2026-07-09T10:00:00+00:00",
            "stoppedAt": None,
            "restartCount": 0,
            "latestOutputFile": None,
            "storagePath": "storage/recordings/CAM-101/2026-07-09/10",
            "lastError": None,
        }


class StubRecordingService:
    async def start_recording(self, camera_id: str, bearer_token: str) -> StubRecordingState:
        return StubRecordingState()

    async def stop_recording(self, camera_id: str) -> dict:
        return {"status": True, "cameraId": camera_id, "recordingStatus": "stopped", "pid": None}

    async def get_status(self, camera_id: str) -> dict:
        return {"status": True, "cameraId": camera_id, "pid": None, "recordingStatus": "not_running"}

    async def list_recordings(self) -> dict:
        return {"status": True, "recorders": [], "count": 0}


def build_app() -> FastAPI:
    app = FastAPI()
    app.state.recording_service = StubRecordingService()
    app.add_middleware(RequestStateMiddleware)
    app.include_router(router)
    return app


class RecorderRouteTests(unittest.TestCase):
    def test_start_recording_route_returns_pid(self) -> None:
        response = TestClient(build_app()).post("/api/v1/recorders/CAM-101/start")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pid"], 12345)
        self.assertEqual(response.json()["recordingStatus"], "recording")

    def test_status_route_returns_not_running(self) -> None:
        response = TestClient(build_app()).get("/api/v1/recorders/CAM-101/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recordingStatus"], "not_running")


if __name__ == "__main__":
    unittest.main()

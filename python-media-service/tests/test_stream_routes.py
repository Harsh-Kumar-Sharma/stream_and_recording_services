import unittest
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes.streams import router


class RequestStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.bearer_token = "token"
        return await call_next(request)


class StubStreamState:
    def to_response(self) -> dict:
        return {
            "status": True,
            "cameraId": "CAM-101",
            "cameraName": "Gantry Camera",
            "streamStatus": "started",
            "streamType": "hls",
            "streamUrl": "http://localhost:8888/cam-CAM-101/index.m3u8",
            "webrtcUrl": "http://localhost:8889/cam-CAM-101/",
            "webrtcWhepUrl": "http://localhost:8889/cam-CAM-101/whep",
            "startedAt": "2026-07-09T10:00:00+00:00",
            "lastError": None,
        }


class StubStreamService:
    async def start_stream(self, camera_id: str, bearer_token: str) -> StubStreamState:
        return StubStreamState()

    async def stop_stream(self, camera_id: str) -> dict:
        return {"status": True, "cameraId": camera_id, "streamStatus": "stopped"}

    async def get_status(self, camera_id: str) -> dict:
        return {
            "status": True,
            "cameraId": camera_id,
            "streamStatus": "inactive",
            "streamUrl": None,
            "webrtcUrl": None,
            "webrtcWhepUrl": None,
        }

    async def list_streams(self) -> dict:
        return {"status": True, "streams": [], "count": 0}


def build_app() -> FastAPI:
    app = FastAPI()
    app.state.stream_service = StubStreamService()
    app.add_middleware(RequestStateMiddleware)
    app.include_router(router)
    return app


class StreamRouteTests(unittest.TestCase):
    def test_start_stream_route_returns_hls_url(self) -> None:
        response = TestClient(build_app()).post("/api/v1/streams/CAM-101/start")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["streamUrl"], "http://localhost:8888/cam-CAM-101/index.m3u8")
        self.assertEqual(response.json()["webrtcUrl"], "http://localhost:8889/cam-CAM-101/")
        self.assertEqual(response.json()["webrtcWhepUrl"], "http://localhost:8889/cam-CAM-101/whep")
        self.assertNotIn("rtsp", str(response.json()).lower())

    def test_stream_status_route(self) -> None:
        response = TestClient(build_app()).get("/api/v1/streams/CAM-101/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["streamStatus"], "inactive")


if __name__ == "__main__":
    unittest.main()

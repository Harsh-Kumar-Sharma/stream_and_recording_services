import unittest
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes.playback import router
from app.core.config import load_settings
from app.services.playback_service import PlaybackService


TEST_STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage" / "test-playback-routes"


def case_storage(name: str) -> Path:
    root = TEST_STORAGE_ROOT / name
    root.mkdir(parents=True, exist_ok=True)
    return root


class RequestStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.bearer_token = "token"
        return await call_next(request)


def build_app(storage_root: Path) -> FastAPI:
    settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    settings.recording.storage_root = storage_root
    app = FastAPI()
    app.state.playback_service = PlaybackService(settings)
    app.add_middleware(RequestStateMiddleware)
    app.include_router(router)
    return app


class PlaybackRouteTests(unittest.TestCase):
    def test_search_route_returns_files(self) -> None:
        storage_root = case_storage("search")
        target_dir = storage_root / "CAM-101" / "2026-07-09" / "10"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "CAM-101_20260709_100000.mp4").write_bytes(b"video")

        response = TestClient(build_app(storage_root)).get("/api/v1/playback/search?cameraId=CAM-101")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["files"]), 1)

    def test_file_route_serves_mp4(self) -> None:
        storage_root = case_storage("serve")
        target_dir = storage_root / "CAM-101" / "2026-07-09" / "10"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "CAM-101_20260709_100000.mp4").write_bytes(b"video")
        app = build_app(storage_root)
        client = TestClient(app)
        token = client.get("/api/v1/playback/search?cameraId=CAM-101").json()["files"][0]["token"]

        response = client.get(f"/api/v1/playback/CAM-101/file?path={token}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"video")

    def test_file_route_blocks_traversal_token(self) -> None:
        response = TestClient(build_app(case_storage("traversal"))).get("/api/v1/playback/CAM-101/file?path=Li4vc2VjcmV0Lm1wNA==")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errorCode"], "INVALID_FILE_PATH")


if __name__ == "__main__":
    unittest.main()

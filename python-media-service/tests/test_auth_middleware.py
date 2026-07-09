import unittest
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.config import load_settings
from app.core.exceptions import AuthServiceUnavailableError, AuthTokenInvalidError
from app.middleware.auth_middleware import BearerTokenMiddleware
from app.schemas.common import SessionInfo


class StubJavaClient:
    def __init__(self, mode: str) -> None:
        self.mode = mode

    async def validate_token(self, token: str) -> SessionInfo:
        if self.mode == "invalid":
            raise AuthTokenInvalidError()
        if self.mode == "unavailable":
            raise AuthServiceUnavailableError()
        return SessionInfo.model_validate({"valid": True, "userId": "USER-101", "username": "harsh"})


def build_app(mode: str = "valid") -> FastAPI:
    settings = load_settings(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    app = FastAPI()
    app.add_middleware(BearerTokenMiddleware, settings=settings, java_client=StubJavaClient(mode))

    @app.get("/protected")
    async def protected(request: Request) -> dict:
        return {"status": True, "userId": request.state.user["user_id"]}

    @app.get("/health")
    async def health() -> dict:
        return {"status": True}

    return app


class AuthMiddlewareTests(unittest.TestCase):
    def test_health_skips_auth(self) -> None:
        response = TestClient(build_app()).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], True)

    def test_missing_token_is_rejected(self) -> None:
        response = TestClient(build_app()).get("/protected")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "Authorization token is required")

    def test_invalid_token_is_rejected(self) -> None:
        response = TestClient(build_app("invalid")).get("/protected", headers={"Authorization": "Bearer bad"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "Invalid or expired session")

    def test_java_unavailable_returns_503(self) -> None:
        response = TestClient(build_app("unavailable")).get("/protected", headers={"Authorization": "Bearer ok"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["message"], "Authentication service unavailable")

    def test_valid_token_continues_request(self) -> None:
        response = TestClient(build_app()).get("/protected", headers={"Authorization": "Bearer ok"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["userId"], "USER-101")


if __name__ == "__main__":
    unittest.main()

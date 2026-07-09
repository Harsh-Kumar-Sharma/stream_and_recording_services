from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import Settings
from app.core.exceptions import AuthServiceUnavailableError, AuthTokenInvalidError
from app.services.java_client import JavaApiClient


PUBLIC_PATHS = {"/health", "/api/v1/health", "/openapi.json", "/docs", "/redoc", "/docs/oauth2-redirect"}


def error_response(status_code: int, message: str, error_code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": False,
            "message": message,
            "errorCode": error_code,
            "details": {},
        },
    )


class BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        settings: Settings,
        java_client: JavaApiClient | None = None,
    ) -> None:
        super().__init__(app)
        self.settings = settings
        self.java_client = java_client or JavaApiClient(settings)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if self._should_skip(request.url.path):
            return await call_next(request)

        if not self.settings.security.enable_bearer_validation:
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            return error_response(401, "Authorization token is required", "AUTH_TOKEN_MISSING")

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return error_response(401, "Authorization token is required", "AUTH_TOKEN_MISSING")

        try:
            session = await self.java_client.validate_token(token.strip())
        except AuthTokenInvalidError as exc:
            return error_response(exc.status_code, exc.message, exc.error_code)
        except AuthServiceUnavailableError as exc:
            return error_response(exc.status_code, exc.message, exc.error_code)

        request.state.user = session.model_dump()
        request.state.bearer_token = token.strip()
        return await call_next(request)

    def _should_skip(self, path: str) -> bool:
        if path in PUBLIC_PATHS:
            return True
        if path.startswith("/docs/"):
            return True
        return False

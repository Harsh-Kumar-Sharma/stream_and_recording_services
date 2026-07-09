import asyncio
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import AuthServiceUnavailableError, AuthTokenInvalidError, CameraNotFoundError, JavaApiError
from app.schemas.camera import CameraDeviceInfo
from app.schemas.common import SessionInfo

logger = logging.getLogger(__name__)


class JavaApiClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = settings
        self.transport = transport
        self.base_url = settings.java_api.base_url.rstrip("/")

    async def validate_token(self, token: str) -> SessionInfo:
        endpoint = self.settings.java_api.session_validate_endpoint
        data = await self._request_json("GET", endpoint, token)

        if data.get("valid") is False:
            raise AuthTokenInvalidError()

        try:
            session = SessionInfo.model_validate(data)
        except ValidationError as exc:
            raise AuthTokenInvalidError() from exc

        if not session.valid:
            raise AuthTokenInvalidError()

        return session

    async def get_camera_device_info(self, camera_id: str, token: str) -> CameraDeviceInfo:
        endpoint = self.settings.java_api.camera_device_info_endpoint.format(camera_id=camera_id)
        data = await self._request_json("GET", endpoint, token)

        try:
            return CameraDeviceInfo.model_validate(data)
        except ValidationError as exc:
            raise JavaApiError("Invalid camera device info response") from exc

    async def _request_json(self, method: str, endpoint: str, token: str) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        timeout = self.settings.java_api.timeout_seconds
        attempts = self.settings.java_api.retry_count + 1

        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
                    response = await client.request(method, url, headers=headers)
                return self._handle_response(response)
            except AuthTokenInvalidError:
                raise
            except CameraNotFoundError:
                raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                logger.warning("Java API request failed on attempt %s/%s: %s", attempt, attempts, exc)
            except JavaApiError as exc:
                last_error = exc
                if exc.status_code < 500 or attempt == attempts:
                    raise
                logger.warning("Java API returned server error on attempt %s/%s: %s", attempt, attempts, exc.message)

            if attempt < attempts:
                await asyncio.sleep(0.1 * attempt)

        raise AuthServiceUnavailableError() from last_error

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code in (401, 403):
            raise AuthTokenInvalidError()
        if response.status_code == 404:
            raise CameraNotFoundError()
        if response.status_code >= 500:
            raise JavaApiError("Java API server error", response.status_code)
        if response.status_code >= 400:
            raise JavaApiError("Java API request rejected", response.status_code)

        try:
            data = response.json()
        except ValueError as exc:
            raise JavaApiError("Java API returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise JavaApiError("Java API returned unexpected response")
        return data

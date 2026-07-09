import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.playback import router as playback_router
from app.api.routes.recorders import router as recorders_router
from app.api.routes.streams import router as streams_router
from app.core.config import get_settings
from app.core.exceptions import MediaServiceError
from app.core.logging import setup_logging
from app.middleware.auth_middleware import BearerTokenMiddleware
from app.services.recording_service import RecordingService
from app.services.playback_service import PlaybackService
from app.services.storage_service import StorageService
from app.services.stream_service import StreamService


settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s environment", settings.app.name, settings.app.environment)
    try:
        yield
    finally:
        await app.state.recording_service.shutdown()


def create_app() -> FastAPI:
    docs_url = None if settings.app.environment == "production" and not settings.security.allow_docs_in_production else "/docs"
    redoc_url = None if docs_url is None else "/redoc"

    app = FastAPI(
        title=settings.app.name,
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_allowed_origins,
        allow_credentials=settings.security.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.stream_service = StreamService(settings)
    app.state.storage_service = StorageService(settings)
    app.state.recording_service = RecordingService(settings)
    app.state.playback_service = PlaybackService(settings)
    app.add_middleware(BearerTokenMiddleware, settings=settings)
    app.include_router(health_router)
    app.include_router(streams_router)
    app.include_router(recorders_router)
    app.include_router(playback_router)

    @app.exception_handler(MediaServiceError)
    async def media_service_error_handler(request: Request, exc: MediaServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": False,
                "message": exc.message,
                "errorCode": exc.error_code,
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled request error path=%s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "status": False,
                "message": "Internal server error",
                "errorCode": "INTERNAL_SERVER_ERROR",
                "details": {},
            },
        )

    return app


app = create_app()

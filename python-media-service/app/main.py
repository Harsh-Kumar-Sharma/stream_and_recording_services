import logging

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.recorders import router as recorders_router
from app.api.routes.streams import router as streams_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.middleware.auth_middleware import BearerTokenMiddleware
from app.services.recording_service import RecordingService
from app.services.stream_service import StreamService


settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    docs_url = None if settings.app.environment == "production" and not settings.security.allow_docs_in_production else "/docs"
    redoc_url = None if docs_url is None else "/redoc"

    app = FastAPI(
        title=settings.app.name,
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
    )
    app.state.stream_service = StreamService(settings)
    app.state.recording_service = RecordingService(settings)
    app.add_middleware(BearerTokenMiddleware, settings=settings)
    app.include_router(health_router)
    app.include_router(streams_router)
    app.include_router(recorders_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info("Starting %s in %s environment", settings.app.name, settings.app.environment)

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.recording_service.shutdown()

    return app


app = create_app()

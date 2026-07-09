import logging
import logging.config
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from app.core.config import Settings

RTSP_CREDENTIALS_RE = re.compile(r"(rtsp://)([^:@/\s]+):([^@/\s]+)@", re.IGNORECASE)


def mask_rtsp_url(value: str) -> str:
    if not value:
        return value

    if not value.lower().startswith("rtsp://"):
        return value

    try:
        parts = urlsplit(value)
        if not parts.username:
            return value
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        username = parts.username or ""
        masked_netloc = f"{username}:****@{host}"
        return urlunsplit((parts.scheme, masked_netloc, parts.path, parts.query, parts.fragment))
    except ValueError:
        return RTSP_CREDENTIALS_RE.sub(r"\1\2:****@", value)


class RtspMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_rtsp_url(record.msg)
        if record.args:
            record.args = tuple(mask_rtsp_url(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True


def setup_logging(settings: Settings) -> None:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "rtsp_mask": {
                "()": RtspMaskingFilter,
            }
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "filters": ["rtsp_mask"],
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "media-service.log"),
                "maxBytes": 10485760,
                "backupCount": 5,
                "formatter": "standard",
                "filters": ["rtsp_mask"],
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": settings.app.log_level,
        },
    }
    logging.config.dictConfig(config)

from __future__ import annotations

import logging
import sys
from typing import Any

from loguru import logger

from app.core.config import get_settings


class InterceptHandler(logging.Handler):
    """Intercept stdlib logging records and route them to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated.
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """Configure loguru for the application.

    - Production / staging: JSON format for structured log aggregation.
    - Development: human-readable coloured format.
    """
    settings = get_settings()

    log_level = "DEBUG" if settings.DEBUG else "INFO"

    # Remove default loguru sink so we can add our own.
    logger.remove()

    if settings.ENVIRONMENT in ("production", "staging"):
        # JSON format — one log entry per line, easy to ship to ELK / Loki etc.
        logger.add(
            sys.stdout,
            level=log_level,
            format="{message}",
            serialize=True,  # loguru built-in JSON serialisation
            enqueue=True,
            backtrace=False,
            diagnose=False,
        )
    else:
        # Human-readable with colours for local development.
        logger.add(
            sys.stdout,
            level=log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
            enqueue=True,
            backtrace=settings.DEBUG,
            diagnose=settings.DEBUG,
        )

    # Intercept all stdlib logging (uvicorn, sqlalchemy, celery, …) and route
    # through loguru so everything ends up in the same sink.
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Ensure common third-party loggers go through our handler.
    for name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy.engine",
        "celery",
        "celery.app.trace",
    ):
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers = [InterceptHandler()]
        stdlib_logger.propagate = False

    logger.info(
        "Logging configured",
        environment=settings.ENVIRONMENT,
        level=log_level,
        format="json" if settings.ENVIRONMENT in ("production", "staging") else "text",
    )


def get_logger(name: str = "app") -> Any:
    """Return a loguru logger bound with the given name."""
    return logger.bind(logger=name)

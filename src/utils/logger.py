"""
RootSight — Structured Logging

Provides agent-scoped loggers with consistent formatting using Rich.
"""

import logging
import sys
from rich.logging import RichHandler
from src.config import settings


_LOG_FORMAT = "%(name)s | %(message)s"
_configured = False


def setup_logging() -> None:
    """Configure root logger with Rich handler. Called once at startup."""
    global _configured
    if _configured:
        return

    root = logging.getLogger("rootsight")
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Rich handler for pretty console output
    handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        markup=True,
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a scoped logger for a module.

    Usage:
        from src.utils.logger import get_logger
        logger = get_logger("agents.rca")
        logger.info("Generating hypotheses...")
    """
    setup_logging()
    return logging.getLogger(f"rootsight.{name}")

"""Logging configuration for structured JSON logging."""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from app.config import settings

# Context variable for request ID (set by middleware)
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds request_id and other context.

    Formats log records as JSON with consistent structure:
    {
        "timestamp": "2025-12-21T10:30:45.123Z",
        "level": "INFO",
        "logger": "app.services.transaction_service",
        "message": "Transaction created",
        "request_id": "abc-123-def",
        "extra_field": "value"
    }
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Add request ID from context if available
        request_id = request_id_context.get()
        if request_id:
            log_record["request_id"] = request_id


def setup_logging() -> None:
    """
    Configure application-wide logging.

    Sets up:
    - JSON formatter for structured logs
    - Console handler to stdout/stderr
    - Log level from configuration
    - Module-level loggers
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create formatter
    if settings.log_format == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        # Text format fallback
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Create console handler (stdout for INFO+, stderr for WARNING+)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger, level: int, message: str, **extra_fields: Any
) -> None:
    """
    Log a message with structured extra fields.

    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **extra_fields: Additional structured fields to include

    Example:
        log_with_context(
            logger,
            logging.INFO,
            "Transaction created",
            transaction_id=123,
            isin="US0378331005",
            transaction_type="BUY"
        )
    """
    logger.log(level, message, extra=extra_fields)

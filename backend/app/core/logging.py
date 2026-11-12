"""Structured JSON logging configuration with request correlation ID tracking."""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable for request correlation ID
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id_ctx", default=None)


class StructuredJsonFormatter(logging.Formatter):
    """Custom JSON formatter producing structured telemetry logs."""

    SENSITIVE_KEYS = {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "authorization",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": correlation_id_ctx.get(),
        }

        # Append extra attributes passed in logger.info(..., extra={...})
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            sanitized_extra = self._sanitize(record.extra)
            log_data.update(sanitized_extra)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive key-values to prevent secret leakage in logs."""
        cleaned = {}
        for k, v in data.items():
            if any(sensitive in k.lower() for sensitive in self.SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]"
            elif isinstance(v, dict):
                cleaned[k] = self._sanitize(v)
            else:
                cleaned[k] = v
        return cleaned


def setup_logging(log_level: str = "INFO") -> None:
    """Configures application-wide structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplication
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)


logger = logging.getLogger("agentra")

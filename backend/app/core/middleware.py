"""Application middleware: Request correlation ID and execution time tracking."""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import correlation_id_ctx, logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware ensuring every request has a correlation ID injected into context and headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract existing X-Request-ID or generate new UUID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        token = correlation_id_ctx.set(request_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = str(duration_ms)

            # Log non-health requests
            if not request.url.path.startswith(("/health", "/ready")):
                logger.info(
                    f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
            return response
        finally:
            correlation_id_ctx.reset(token)

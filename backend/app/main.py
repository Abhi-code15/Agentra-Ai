"""FastAPI application entry point, lifecycle management, and exception handling."""
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.exceptions import AgentraException
from app.core.logging import correlation_id_ctx, logger, setup_logging
from app.core.middleware import CorrelationIdMiddleware
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    setup_logging(settings.LOG_LEVEL)
    logger.info("Initializing Agentra backend services...")

    # Ensure storage directory exists
    os.makedirs(settings.STORAGE_DIRECTORY, exist_ok=True)
    logger.info(f"Verified storage directory at: {settings.STORAGE_DIRECTORY}")

    yield

    logger.info("Shutting down Agentra backend services...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise AI Governance and Document Intelligence Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Correlation ID Middleware (must be added before CORS so request_id is always available)
app.add_middleware(CorrelationIdMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(AgentraException)
async def agentra_exception_handler(request: Request, exc: AgentraException) -> JSONResponse:
    request_id = correlation_id_ctx.get()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "meta": {"request_id": request_id},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = correlation_id_ctx.get()
    formatted_errors = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        formatted_errors.append({"field": loc, "message": err.get("msg")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload failed validation.",
                "details": formatted_errors,
            },
            "meta": {"request_id": request_id},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = correlation_id_ctx.get()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": [],
            },
            "meta": {"request_id": request_id},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = correlation_id_ctx.get()
    logger.exception(f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred. Please try again later.",
                "details": [],
            },
            "meta": {"request_id": request_id},
        },
    )


# Mount API v1 Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# System Probes
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Liveness probe indicating process availability."""
    return {"status": "healthy", "service": "agentra-api"}


@app.get("/ready", tags=["System"])
async def readiness_check() -> dict:
    """Readiness probe checking database connectivity and storage directory."""
    checks = {}

    # Check Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "connected"
    except Exception as e:
        logger.error(f"Readiness database probe failed: {str(e)}")
        checks["database"] = "disconnected"

    # Check Storage Writable
    try:
        os.makedirs(settings.STORAGE_DIRECTORY, exist_ok=True)
        test_file = os.path.join(settings.STORAGE_DIRECTORY, f".probe_{uuid.uuid4().hex}")
        with open(test_file, "w") as f:
            f.write("probe")
        os.remove(test_file)
        checks["storage"] = "writable"
    except Exception as e:
        logger.error(f"Readiness storage probe failed: {str(e)}")
        checks["storage"] = "read_only_or_missing"

    all_ready = all(v in ("connected", "writable") for v in checks.values())
    if not all_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}

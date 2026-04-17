import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import log_with_context, request_id_context, setup_logging
from app.services.etf_breakdown_service import load_breakdowns
from app.routers import (
    analytics,
    asset_snapshots,
    etf_breakdown,
    isin_metadata,
    other_assets,
    position_values,
    transactions,
)
from app.routers import settings as settings_router

# Initialize logging on module import
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info(
        "Application starting",
        extra={
            "project_name": settings.project_name,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "log_format": settings.log_format,
        },
    )
    data_dir = Path(settings.etf_data_dir)
    if data_dir.exists():
        load_breakdowns(data_dir)
    else:
        logger.warning("ETF data directory not found, breakdown endpoints will return 404: %s", data_dir)
    yield
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="API for tracking ETF portfolio transactions with cost basis calculations",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
    root_path="/api",
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    Add unique request ID to each request for distributed tracing.

    Sets request_id in context variable for use in all logs during request.
    """
    request_id = str(uuid.uuid4())
    request_id_context.set(request_id)

    # Add to response headers for client-side tracing
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Log all HTTP requests and responses with timing.

    Logs:
    - Request: method, path, client IP
    - Response: status code, duration
    - Errors: exception details
    """
    start_time = time.time()
    request_id = request_id_context.get()

    # Log request
    log_with_context(
        logger,
        logging.INFO,
        "HTTP request received",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_host=request.client.host if request.client else None,
        request_id=request_id,
    )

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        log_level = logging.INFO if response.status_code < 400 else logging.WARNING
        log_with_context(
            logger,
            log_level,
            "HTTP request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )

        return response

    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000

        log_with_context(
            logger,
            logging.ERROR,
            "HTTP request failed with unhandled exception",
            method=request.method,
            path=request.url.path,
            duration_ms=round(duration_ms, 2),
            error_type=type(exc).__name__,
            error_message=str(exc),
            request_id=request_id,
        )

        # Re-raise to let FastAPI handle
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.

    Logs exception details and returns 500 error response.
    """
    request_id = request_id_context.get()

    log_with_context(
        logger,
        logging.ERROR,
        "Unhandled exception caught by global handler",
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_api_key_db_map = settings.api_key_db_map_parsed


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Validate API key and resolve the corresponding database URL.

    When API_KEY_DB_MAP is configured, each key maps to a different database.
    When empty (local dev), all requests pass through without auth.
    Falls back to legacy single API_KEY if API_KEY_DB_MAP is not set.
    """
    if request.url.path in ("/", ) or request.url.path.endswith("/health"):
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)

    if not _api_key_db_map:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    db_url = _api_key_db_map.get(api_key) if api_key else None
    if db_url is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API key"},
        )
    request.state.database_url = db_url
    return await call_next(request)


# Include routers
app.include_router(transactions.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(isin_metadata.router, prefix=settings.api_v1_prefix)
app.include_router(position_values.router, prefix=settings.api_v1_prefix)
app.include_router(other_assets.router, prefix=settings.api_v1_prefix)
app.include_router(asset_snapshots.router, prefix=settings.api_v1_prefix)
app.include_router(settings_router.router, prefix=settings.api_v1_prefix)
app.include_router(etf_breakdown.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "ETF Portfolio Tracker API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["health"])
@app.get("/v1/health", tags=["health"])
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy"}

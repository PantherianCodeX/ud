# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Note: HealthCheck imported from base models for Phase 1
# Once workspace packages are properly installed, use: from udocket_domain import HealthCheck
# Temporary inline model for Phase 1
from pydantic import BaseModel, ConfigDict, Field

from udocket_api.core import UDocketError, check_db_health, configure_logging, init_db, settings
from udocket_api.workflow import register_workflows


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    database: bool = Field(..., description="Database connectivity status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "environment": "development",
                "database": True,
            }
        }
    )


# Configure logging on module import
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan context manager.

    Args:
        _app: FastAPI application instance (unused but required by lifespan protocol).

    Yields:
        None: Yields after startup, returns after shutdown.
    """
    # Startup
    logger.info("application_starting", version=settings.app_version, environment=settings.environment)

    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.exception("database_initialization_failed", error=str(e))

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Legal interview analysis and documentation platform",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(UDocketError)
def udocket_exception_handler(request: Request, exc: UDocketError) -> JSONResponse:
    """Handle custom uDocket exceptions.

    Args:
        request: The incoming request.
        exc: The UDocket exception that was raised.

    Returns:
        JSON response with error details.
    """
    logger.error(
        "application_error",
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> HealthCheck:
    """Health check endpoint.

    Returns:
        HealthCheck model with service status, version, environment, and database connectivity.
    """
    db_healthy = await check_db_health()

    return HealthCheck(
        status="healthy" if db_healthy else "unhealthy",
        version=settings.app_version,
        environment=settings.environment,
        database=db_healthy,
    )


# Register workflow routers
register_workflows(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "udocket_api.main:app",
        host="0.0.0.0",  # noqa: S104 - Required for container networking
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use structlog instead
    )

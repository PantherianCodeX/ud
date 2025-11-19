# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Base models with common fields and configuration."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class BaseEntity(BaseModel):
    """Base model for entities with ID and timestamps."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=_utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=_utc_now, description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    )


class BaseRequest(BaseModel):
    """Base model for API requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
    )


class BaseResponse(BaseModel):
    """Base model for API responses."""

    model_config = ConfigDict(
        from_attributes=True,
    )


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

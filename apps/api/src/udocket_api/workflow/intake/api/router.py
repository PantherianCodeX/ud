# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""FastAPI routes for the intake workflow slice."""

from __future__ import annotations

import uuid  # noqa: TC003 - FastAPI path params rely on runtime UUID parsing
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from udocket_api.workflow.intake import schemas as intake_schemas
from udocket_api.workflow.intake.service import IntakeService

router = APIRouter(prefix="/api/v1/intake", tags=["intake"])
_service = IntakeService()


def get_intake_service() -> IntakeService:
    """Dependency injection helper.

    Returns:
        IntakeService: Singleton instance.
    """
    return _service


@router.post("/submissions", response_model=intake_schemas.IntakeRecord, status_code=http_status.HTTP_201_CREATED)
def submit_intake(
    payload: intake_schemas.IntakeRequest,
    service: Annotated[IntakeService, Depends(get_intake_service)],
) -> intake_schemas.IntakeRecord:
    """Create a new intake submission.

    Returns:
        IntakeRecord: Newly created record.
    """
    return service.submit(payload)


@router.get("/submissions", response_model=list[intake_schemas.IntakeRecord])
def list_intake_records(
    service: Annotated[IntakeService, Depends(get_intake_service)],
) -> list[intake_schemas.IntakeRecord]:
    """List all intake submissions in creation order.

    Returns:
        list[IntakeRecord]: Records sorted by creation timestamp.
    """
    return service.list_records()


@router.patch("/submissions/{record_id}", response_model=intake_schemas.IntakeRecord)
def update_intake_status(
    record_id: uuid.UUID,
    *,
    status: str,
    service: Annotated[IntakeService, Depends(get_intake_service)],
) -> intake_schemas.IntakeRecord:
    """Update the state of a submission.

    Returns:
        IntakeRecord: Updated record.

    Raises:
        HTTPException: If the record is not found.
    """
    try:
        return service.update_status(record_id, status=status)
    except KeyError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/status", response_model=intake_schemas.IntakeStatus)
def get_intake_status(service: Annotated[IntakeService, Depends(get_intake_service)]) -> intake_schemas.IntakeStatus:
    """Return aggregate status metrics."""
    return service.get_status()

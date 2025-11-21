# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Matter router."""

from __future__ import annotations

import uuid  # noqa: TC003 - FastAPI path params rely on runtime UUID parsing
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from udocket_api.workflow.matters import schemas as matters_schemas  # noqa: TC001 - FastAPI requires runtime schema
from udocket_api.workflow.matters.service import MattersService
from udocket_domain import Matter

router = APIRouter(prefix="/api/v1/matters", tags=["matters"])
_service = MattersService()


def get_matters_service() -> MattersService:
    """Return the shared service instance."""
    return _service


@router.post("", response_model=Matter, status_code=status.HTTP_201_CREATED)
def create_matter(
    payload: matters_schemas.MatterCreateRequest,
    service: Annotated[MattersService, Depends(get_matters_service)],
) -> Matter:
    """Create a matter.

    Returns:
        Matter: Newly created matter entity.
    """
    return service.create(payload)


@router.get("", response_model=list[Matter])
def list_matters(service: Annotated[MattersService, Depends(get_matters_service)]) -> list[Matter]:
    """List all matters.

    Returns:
        list[Matter]: Sorted matter list.
    """
    return service.list()


@router.get("/{matter_id}", response_model=Matter)
def get_matter(
    matter_id: uuid.UUID,
    service: Annotated[MattersService, Depends(get_matters_service)],
) -> Matter:
    """Return a single matter by ID.

    Returns:
        Matter: Requested matter.

    Raises:
        HTTPException: If the matter does not exist.
    """
    try:
        return service.get(matter_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

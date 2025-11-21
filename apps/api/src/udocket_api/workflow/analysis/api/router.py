# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Analysis routes."""

from __future__ import annotations

import uuid  # noqa: TC003 - FastAPI path params rely on runtime UUID parsing
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from udocket_api.workflow.analysis import schemas as analysis_schemas  # noqa: TC001 - FastAPI requires runtime schema
from udocket_api.workflow.analysis.service import AnalysisService
from udocket_domain import MatterAnalysis

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])
_service = AnalysisService()


def get_analysis_service() -> AnalysisService:
    """Return the shared analysis service.

    Returns:
        AnalysisService: Singleton service instance.
    """
    return _service


@router.post("", response_model=MatterAnalysis, status_code=status.HTTP_201_CREATED)
def run_analysis(
    payload: analysis_schemas.AnalysisRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> MatterAnalysis:
    """Trigger an analysis run for a matter.

    Args:
        payload: Validated analysis request body.
        service: Dependency-injected analysis service instance.

    Returns:
        MatterAnalysis: Newly generated analysis artifact.
    """
    return service.run_analysis(payload)


@router.get("/{matter_id}", response_model=MatterAnalysis)
def get_analysis(
    matter_id: uuid.UUID,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> MatterAnalysis:
    """Fetch the cached analysis for a matter.

    Args:
        matter_id: Identifier for the matter requested.
        service: Dependency-injected analysis service instance.

    Returns:
        MatterAnalysis: Cached analysis.

    Raises:
        HTTPException: If no analysis exists for the matter.
    """
    try:
        return service.get_analysis(matter_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

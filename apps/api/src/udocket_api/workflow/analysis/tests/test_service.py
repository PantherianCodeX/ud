# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
"""Analysis service tests."""

from uuid import uuid4

import pytest

from udocket_api.workflow.analysis.schemas import AnalysisRequest
from udocket_api.workflow.analysis.service import AnalysisService


def test_run_analysis_creates_embedding() -> None:
    """Running analysis caches embedding data."""
    service = AnalysisService()
    matter_id = uuid4()
    analysis = service.run_analysis(
        AnalysisRequest(
            matter_id=matter_id,
            transcript="Client testimony referencing multiple facts for summary.",
        )
    )

    assert analysis.matter_id == matter_id
    assert analysis.embedding is not None


def test_get_missing_analysis_raises() -> None:
    """Fetching a missing analysis raises KeyError."""
    service = AnalysisService()
    with pytest.raises(KeyError):
        service.get_analysis(uuid4())

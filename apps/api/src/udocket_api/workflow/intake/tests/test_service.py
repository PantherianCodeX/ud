# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Unit tests for intake service."""

from uuid import uuid4

import pytest

from udocket_api.workflow.intake.schemas import IntakeRequest, IntakeWorkflowStatus
from udocket_api.workflow.intake.service import IntakeService


def test_submit_persists_record() -> None:
    """Submitting an intake yields a record stored in the service."""
    service = IntakeService()
    record = service.submit(
        IntakeRequest(
            matter_title="Matter 1",
            summary="Initial consultation summary",
            client_name="Client A",
        )
    )

    assert record.id in {item.id for item in service.list_records()}


def test_update_missing_record_raises() -> None:
    """Updating a non-existent record raises KeyError."""
    service = IntakeService()
    with pytest.raises(KeyError):
        service.update_status(uuid4(), status=IntakeWorkflowStatus.COMPLETE)


def test_status_counts_pending_and_completed() -> None:
    """Aggregate status reflects completed versus pending records."""
    service = IntakeService()
    record = service.submit(
        IntakeRequest(
            matter_title="Matter 2",
            summary="Summary",
            client_name="Client B",
        )
    )
    service.update_status(record.id, status=IntakeWorkflowStatus.COMPLETE)

    stats = service.get_status()
    assert stats.total_records == 1
    assert stats.completed_records == 1
    assert stats.pending_records == 0


def test_seed_raises_type_error_for_non_iterable() -> None:
    """Seed should raise a TypeError when provided a non-iterable."""
    service = IntakeService()
    with pytest.raises(TypeError):
        # Intentionally pass invalid value to ensure defensive branch triggers.
        service.seed(records=42)  # type: ignore[arg-type]  # JUSTIFIED: verifying TypeError on non-iterable input

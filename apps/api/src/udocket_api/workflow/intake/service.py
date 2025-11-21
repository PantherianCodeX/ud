# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Domain logic for the intake workflow slice."""

from __future__ import annotations

import uuid
from collections import abc
from typing import cast

from udocket_api.workflow.intake import schemas as intake_schemas


class IntakeService:
    """In-memory implementation for managing intake records."""

    def __init__(self) -> None:
        """Initialize storage."""
        self._records: dict[uuid.UUID, intake_schemas.IntakeRecord] = {}

    def submit(self, request: intake_schemas.IntakeRequest) -> intake_schemas.IntakeRecord:
        """Create a new intake record.

        Returns:
            IntakeRecord: Newly created record.
        """
        record = intake_schemas.IntakeRecord(
            matter_title=request.matter_title,
            summary=request.summary,
            client_name=request.client_name,
        )
        self._records[record.id] = record
        return record

    def update_status(
        self, record_id: uuid.UUID, *, status: str
    ) -> intake_schemas.IntakeRecord:
        """Update the workflow status for a record.

        Returns:
            IntakeRecord: Updated record.

        Raises:
            KeyError: If the record does not exist.
            TypeError: If the identifier is not a UUID.
        """
        if not isinstance(cast(object, record_id), uuid.UUID):
            msg = "record_id must be a UUID"
            raise TypeError(msg)
        if not (record := self._records.get(record_id)):
            msg = f"Intake record {record_id} not found"
            raise KeyError(msg)

        updated = record.model_copy(update={"status": status})
        self._records[record_id] = updated
        return updated

    def list_records(self) -> list[intake_schemas.IntakeRecord]:
        """Return all records sorted by creation time."""
        return sorted(self._records.values(), key=lambda record: record.created_at)

    def get_status(self) -> intake_schemas.IntakeStatus:
        """Compute aggregate statistics.

        Returns:
            IntakeStatus: Aggregate counts.
        """
        pending = sum(1 for record in self._records.values() if record.status != "complete")
        completed = sum(1 for record in self._records.values() if record.status == "complete")
        return intake_schemas.IntakeStatus(
            total_records=len(self._records),
            pending_records=pending,
            completed_records=completed,
        )

    def reset(self) -> None:
        """Clear all records (used in tests)."""
        self._records.clear()

    def seed(self, records: abc.Iterable[intake_schemas.IntakeRecord]) -> None:
        """Load records (useful for fixtures).

        Raises:
            TypeError: If the argument is not iterable.
        """
        if not isinstance(cast(object, records), abc.Iterable):
            msg = "records must be iterable"
            raise TypeError(msg)
        for record in records:
            self._records[record.id] = record

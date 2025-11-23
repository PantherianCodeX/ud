# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Intake workflow API tests."""

from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient


def _create_submission(client: TestClient) -> dict[str, object]:
    payload = {
        "matter_title": "Sample Matter",
        "summary": "Client describes initial consultation details.",
        "client_name": "Jane Smith",
    }
    response = client.post("/api/v1/intake/submissions", json=payload)
    assert response.status_code == 201
    return cast("dict[str, object]", response.json())


def test_submit_intake(client: TestClient) -> None:
    """Submitting intake returns a persisted record."""
    record = _create_submission(client)

    assert UUID(str(record["id"]))
    assert record["status"] == "pending"
    assert record["matter_title"] == "Sample Matter"


def test_list_intake_records(client: TestClient) -> None:
    """Records appear in listing order."""
    _create_submission(client)
    _create_submission(client)

    response = client.get("/api/v1/intake/submissions")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2


def test_update_intake_status(client: TestClient) -> None:
    """Status updates modify existing records."""
    record = _create_submission(client)
    response = client.patch(f"/api/v1/intake/submissions/{record['id']}?status=complete")

    assert response.status_code == 200
    assert response.json()["status"] == "complete"


def test_get_status_summary(client: TestClient) -> None:
    """Aggregate status metrics reflect record state."""
    record = _create_submission(client)
    client.patch(f"/api/v1/intake/submissions/{record['id']}?status=complete")

    response = client.get("/api/v1/intake/status")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_records"] == 1
    assert stats["completed_records"] == 1
    assert stats["pending_records"] == 0

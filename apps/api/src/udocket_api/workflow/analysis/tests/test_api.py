# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Analysis workflow tests."""

from uuid import uuid4

from fastapi.testclient import TestClient


def test_run_analysis(client: TestClient) -> None:
    """Running analysis stores result keyed by matter."""
    payload = {
        "matter_id": str(uuid4()),
        "transcript": "Client described facts. Opposing party contested events.",
    }
    response = client.post("/api/v1/analysis", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["matter_id"] == payload["matter_id"]
    assert body["summary"]


def test_get_analysis(client: TestClient) -> None:
    """Cached analyses can be retrieved."""
    payload = {
        "matter_id": str(uuid4()),
        "transcript": "Initial transcript content. Additional detail for testing.",
    }
    create_response = client.post("/api/v1/analysis", json=payload)
    assert create_response.status_code == 201

    response = client.get(f"/api/v1/analysis/{payload['matter_id']}")
    assert response.status_code == 200
    assert response.json()["matter_id"] == payload["matter_id"]

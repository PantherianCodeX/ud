# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Matters workflow API tests."""

from typing import cast
from uuid import UUID

from fastapi.testclient import TestClient


def _create_matter(client: TestClient) -> dict[str, object]:
    payload = {
        "title": "Doe v Doe",
        "description": "Initial divorce filing",
        "matter_type": "family_law",
    }
    response = client.post("/api/v1/matters", json=payload)
    assert response.status_code == 201
    return cast("dict[str, object]", response.json())


def test_create_matter(client: TestClient) -> None:
    """Creating matters returns the domain model."""
    matter = _create_matter(client)
    assert UUID(str(matter["id"]))
    assert matter["title"] == "Doe v Doe"


def test_list_matters(client: TestClient) -> None:
    """Listing returns created matters."""
    _create_matter(client)
    _create_matter(client)

    response = client.get("/api/v1/matters")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2


def test_get_matter_by_id(client: TestClient) -> None:
    """Single matters can be fetched."""
    matter = _create_matter(client)
    response = client.get(f"/api/v1/matters/{matter['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == matter["id"]

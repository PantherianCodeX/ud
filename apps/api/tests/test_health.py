# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Tests for health check endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint returns correct response."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["version"] == "0.1.0"
    assert data["environment"] in ["development", "staging", "production"]
    assert isinstance(data["database"], bool)


def test_health_check_structure(client: TestClient):
    """Test health check response has required fields."""
    response = client.get("/health")
    data = response.json()

    required_fields = ["status", "version", "environment", "database"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

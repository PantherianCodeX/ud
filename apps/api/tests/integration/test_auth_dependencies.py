"""Integration tests for auth dependency helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from udocket_api.platform.auth.dependencies import require_role
from udocket_api.platform.auth.jwt import UserStub, create_access_token

if TYPE_CHECKING:
    from collections.abc import Generator

app = FastAPI()
AdminUser = Annotated[UserStub, Depends(require_role("admin"))]


@app.get("/admin")
def admin_route(_: AdminUser) -> dict[str, str]:
    """Route protected by the `require_role` dependency.

    Returns:
        dict[str, str]: Success payload when authorization succeeds.
    """
    return {"status": "ok"}


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a lightweight FastAPI TestClient for dependency validation.

    Yields:
        TestClient: HTTP client bound to the in-memory FastAPI app.
    """
    with TestClient(app) as test_client:
        yield test_client


def _auth_headers(*roles: str) -> dict[str, str]:
    """Create Authorization headers for the provided roles.

    Returns:
        dict[str, str]: HTTP headers containing a bearer token.
    """
    user = UserStub(
        id=uuid4(),
        email="integration@example.com",
        full_name="Integration Tester",
        roles=list(roles) or ["user"],
        is_active=True,
    )
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_require_role_returns_403_for_missing_role(client: TestClient) -> None:
    """Users lacking the required role should receive a 403 response."""
    response = client.get("/admin", headers=_auth_headers("user"))
    assert response.status_code == 403
    assert response.json()["detail"] == "Role 'admin' required"


def test_require_role_allows_authorized_user(client: TestClient) -> None:
    """Users with the required role should be able to reach the route."""
    response = client.get("/admin", headers=_auth_headers("admin", "user"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

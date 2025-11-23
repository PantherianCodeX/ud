from __future__ import annotations

import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

if TYPE_CHECKING:
    from fastapi import Request

from udocket_api.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    UDocketError,
    ValidationError,
)
from udocket_api.main import udocket_exception_handler

pytestmark = pytest.mark.unit


def _build_request(path: str = "/unit/test") -> Request:
    """Create a lightweight request mimic for the exception handler.

    Returns:
        Request: Minimal object carrying a ``url.path`` attribute.
    """

    class DummyURL(SimpleNamespace):
        """Minimal object exposing the FastAPI ``url.path`` interface."""

        def __init__(self, path: str) -> None:
            super().__init__(path=path)
            self.path = path

    return cast("Request", SimpleNamespace(url=DummyURL(path=path)))


def _assert_handler_response(exc: UDocketError) -> None:
    """Assert that the FastAPI handler returns the expected payload."""
    request = _build_request()
    response = udocket_exception_handler(request, exc)
    assert response.status_code == 400
    payload = json.loads(bytes(response.body).decode())
    assert payload["error_code"] == exc.error_code
    assert payload["message"] == exc.message


def test_udocket_error_properties() -> None:
    """Ensure the base UDocketError captures the provided message and code."""
    base = UDocketError("base failure", error_code="BASE")
    assert base.message == "base failure"
    assert base.error_code == "BASE"


@pytest.mark.parametrize(
    ("exception_cls", "expected_code"),
    [
        (ResourceNotFoundError("Matter", "123"), "RESOURCE_NOT_FOUND"),
        (DatabaseError("boom"), "DATABASE_ERROR"),
        (ValidationError("invalid"), "VALIDATION_ERROR"),
        (AuthenticationError(), "AUTHENTICATION_ERROR"),
        (AuthorizationError(), "AUTHORIZATION_ERROR"),
    ],
)
def test_specific_exceptions_have_codes_and_handler(exception_cls: UDocketError, expected_code: str) -> None:
    """Verify subclass-specific error codes and handler responses."""
    assert exception_cls.error_code == expected_code
    _assert_handler_response(exception_cls)

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from udocket_api.core.config import settings
from udocket_api.core.exceptions import AuthenticationError
from udocket_api.platform.auth.jwt import UserStub, create_access_token, decode_access_token

pytestmark = pytest.mark.unit


def _build_user() -> UserStub:
    """Create a deterministic user stub for token tests.

    Returns:
        UserStub: Default admin-capable user for token scenarios.
    """
    return UserStub(
        id=uuid4(),
        email="jwt-test@example.com",
        full_name="JWT Tester",
        roles=["user", "admin"],
        is_active=True,
    )


def test_create_and_decode_token_round_trip() -> None:
    """JWT creation and decoding should round trip with preserved data."""
    user = _build_user()
    token = create_access_token(user)

    decoded = decode_access_token(token)

    assert decoded.user_id == user.id
    assert decoded.email == user.email
    assert decoded.roles == user.roles
    assert decoded.exp is not None
    assert decoded.exp.tzinfo is UTC
    assert decoded.exp > datetime.now(UTC)


def test_decode_access_token_rejects_invalid_signature() -> None:
    """Tampered tokens should raise an authentication error."""
    user = _build_user()
    valid_token = create_access_token(user)
    tampered_token = f"{valid_token}x"

    with pytest.raises(AuthenticationError, match="Token validation failed"):
        decode_access_token(tampered_token)


def test_decode_access_token_rejects_missing_email() -> None:
    """Tokens without an email claim should be rejected."""
    payload = {
        "user_id": str(uuid4()),
        "roles": ["user"],
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "iat": datetime.now(UTC),
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(AuthenticationError, match="Invalid token payload"):
        decode_access_token(token)


def test_decode_access_token_rejects_bad_user_id() -> None:
    """Tokens with malformed user IDs should be rejected."""
    payload = {
        "user_id": "not-a-uuid",
        "email": "bad-user@example.com",
        "roles": ["user"],
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "iat": datetime.now(UTC),
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(AuthenticationError, match="Invalid token format"):
        decode_access_token(token)

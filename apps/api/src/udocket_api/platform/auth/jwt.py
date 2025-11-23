# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""JWT token handling (Keycloak stub).

NOTE: This is a simplified JWT implementation for Phase 1 development.
Full Keycloak OIDC integration is planned for Phase 2+.
See ROADMAP.md Phase 2 for Keycloak integration details.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import InvalidTokenError
from pydantic import BaseModel, Field

from udocket_api.core.config import settings
from udocket_api.core.exceptions import AuthenticationError


class TokenData(BaseModel):
    """Data contained in a JWT token."""

    user_id: UUID = Field(..., description="User identifier")
    email: str = Field(..., description="User email")
    roles: list[str] = Field(default_factory=list, description="User roles")
    exp: datetime | None = Field(None, description="Expiration timestamp")


class UserStub(BaseModel):
    """Stub user model for Phase 1 development."""

    id: UUID
    email: str
    full_name: str
    roles: list[str] = Field(default_factory=list)
    is_active: bool = True


def create_access_token(user: UserStub) -> str:
    """Create a JWT access token for a user.

    Args:
        user: User to create token for

    Returns:
        Encoded JWT token string
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "roles": user.roles,
        "exp": expire,
        "iat": datetime.now(UTC),
    }

    encoded: str = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT access token.

    Args:
        token: Encoded JWT token string

    Returns:
        Decoded token data

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        user_id = UUID(payload.get("user_id"))
        email = payload.get("email")
        roles = payload.get("roles", [])
        exp = payload.get("exp")

        if not user_id or not email:
            msg = "Invalid token payload"
            raise AuthenticationError(msg)

        return TokenData(
            user_id=user_id,
            email=email,
            roles=roles,
            exp=datetime.fromtimestamp(exp, tz=UTC) if exp else None,
        )

    except InvalidTokenError as e:
        msg = f"Token validation failed: {e!s}"
        raise AuthenticationError(msg) from e
    except ValueError as e:
        msg = f"Invalid token format: {e!s}"
        raise AuthenticationError(msg) from e

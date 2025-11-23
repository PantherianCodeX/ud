# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""FastAPI dependencies for authentication.

NOTE: This is a stub implementation for Phase 1.
Full Keycloak OIDC integration planned for Phase 2+.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from udocket_api.core.exceptions import AuthenticationError

from .jwt import UserStub, decode_access_token

# Security scheme
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> UserStub:
    """FastAPI dependency to get current authenticated user.

    Validates JWT token and returns user information.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Current user information

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = decode_access_token(credentials.credentials)

        # In Phase 1, we reconstruct a stub user from token data
        # In Phase 2+, this will query Keycloak or a user service
        email_value = str(token_data.email)
        return UserStub(
            id=token_data.user_id,
            email=email_value,
            full_name=email_value.split("@", maxsplit=1)[0],  # Stub
            roles=token_data.roles,
            is_active=True,
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def require_role(
    required_role: str,
) -> Callable[[UserStub], UserStub]:
    """FastAPI dependency factory to require a specific role.

    Args:
        required_role: Role required to access endpoint

    Returns:
        Dependency function that checks user role
    """

    def role_checker(user: Annotated[UserStub, Depends(get_current_user)]) -> UserStub:
        """Validate that ``user`` possesses ``required_role``.

        Args:
            user: Authenticated user resolved by ``get_current_user``.

        Returns:
            UserStub: The same ``user`` instance when authorized.

        Raises:
            HTTPException: If ``user`` is missing the required role.
        """
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user

    return role_checker

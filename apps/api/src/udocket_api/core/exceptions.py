# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Custom exception classes for the application."""


class UDocketError(Exception):
    """Base exception for all uDocket errors.

    Args:
        message: Human-readable error message.
        error_code: Optional machine-readable error code for API responses.
    """

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize the base uDocket error."""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ResourceNotFoundError(UDocketError):
    """Raised when a requested resource is not found.

    Args:
        resource_type: Type of resource (e.g., "Matter", "User").
        resource_id: Identifier of the resource.
    """

    def __init__(self, resource_type: str, resource_id: str) -> None:
        """Initialize the resource not found error."""
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND")


class DatabaseError(UDocketError):
    """Raised when a database operation fails.

    Args:
        message: Description of the database error.
    """

    def __init__(self, message: str) -> None:
        """Initialize the database error."""
        super().__init__(message, error_code="DATABASE_ERROR")


class ValidationError(UDocketError):
    """Raised when validation fails.

    Args:
        message: Description of the validation error.
    """

    def __init__(self, message: str) -> None:
        """Initialize the validation error."""
        super().__init__(message, error_code="VALIDATION_ERROR")


class AuthenticationError(UDocketError):
    """Raised when authentication fails.

    Args:
        message: Optional custom error message.
    """

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize the authentication error."""
        super().__init__(message, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(UDocketError):
    """Raised when authorization fails.

    Args:
        message: Optional custom error message.
    """

    def __init__(self, message: str = "Insufficient permissions") -> None:
        """Initialize the authorization error."""
        super().__init__(message, error_code="AUTHORIZATION_ERROR")

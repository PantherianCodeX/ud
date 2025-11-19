# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Custom exception classes for the application."""


class UDocketException(Exception):
    """Base exception for all uDocket errors."""
    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ResourceNotFoundError(UDocketException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND")


class DatabaseError(UDocketException):
    """Raised when a database operation fails."""
    def __init__(self, message: str):
        super().__init__(message, error_code="DATABASE_ERROR")


class ValidationError(UDocketException):
    """Raised when validation fails."""
    def __init__(self, message: str):
        super().__init__(message, error_code="VALIDATION_ERROR")


class AuthenticationError(UDocketException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(UDocketException):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, error_code="AUTHORIZATION_ERROR")

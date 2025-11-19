# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Core infrastructure modules."""
from .config import settings
from .database import Base, async_session_maker, check_db_health, engine, get_db, init_db
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    UDocketException,
    ValidationError,
)
from .logging import configure_logging, get_logger

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "Base",
    "DatabaseError",
    "ResourceNotFoundError",
    "UDocketException",
    "ValidationError",
    "async_session_maker",
    "check_db_health",
    "configure_logging",
    "engine",
    "get_db",
    "get_logger",
    "init_db",
    "settings",
]

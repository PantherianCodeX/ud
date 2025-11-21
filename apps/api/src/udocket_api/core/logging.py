# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Structured logging configuration with structlog."""

import logging
import sys

import structlog
from structlog.types import EventDict, Processor

from .config import settings


def add_app_context(
    _logger: structlog.stdlib.BoundLogger,
    _method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add application context to all log entries.

    Args:
        _logger: Logger instance (unused, required by protocol).
        _method_name: Method name (unused, required by protocol).
        event_dict: Event dictionary to enrich.

    Returns:
        Enriched event dictionary with app context.
    """
    event_dict["app_name"] = settings.app_name
    event_dict["app_version"] = settings.app_version
    event_dict["environment"] = settings.environment
    return event_dict


def configure_logging() -> None:
    """Configure structlog with appropriate processors."""
    # Determine processors based on environment
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty console output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


# Get logger instance
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured BoundLogger instance.
    """
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger

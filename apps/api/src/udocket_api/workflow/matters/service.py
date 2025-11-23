# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Service layer for matter operations."""

from __future__ import annotations

import uuid
from typing import cast

from udocket_api.workflow.matters import schemas as matters_schemas
from udocket_domain import Matter


class MattersService:
    """In-memory matter storage and operations.

    Provides CRUD operations for legal matters using an in-memory
    dictionary store. Suitable for development and testing.
    """

    def __init__(self) -> None:
        """Initialize the service with empty storage."""
        self._matters: dict[uuid.UUID, Matter] = {}

    def create(self, payload: matters_schemas.MatterCreateRequest) -> Matter:
        """Create and return a new matter.

        Args:
            payload: Validated request payload from the API layer.

        Returns:
            Matter: Newly created entity.

        Raises:
            TypeError: If the payload is not a MatterCreateRequest.
        """
        if not isinstance(cast("object", payload), matters_schemas.MatterCreateRequest):
            msg = "payload must be a MatterCreateRequest"
            raise TypeError(msg)
        matter = Matter(
            title=payload.title,
            description=payload.description,
            matter_type=payload.matter_type,
            client_id=None,
        )
        self._matters[matter.id] = matter
        return matter

    def list(self) -> list[Matter]:
        """Return all matters sorted by creation time.

        Returns:
            list[Matter]: Chronologically ordered matter list.
        """
        return sorted(self._matters.values(), key=lambda matter: matter.created_at)

    def get(self, matter_id: uuid.UUID) -> Matter:
        """Return a single matter.

        Args:
            matter_id: Identifier for the matter record.

        Returns:
            Matter: Stored matter instance.

        Raises:
            KeyError: If the matter is missing.
            TypeError: If the identifier is not a UUID.
        """
        if not isinstance(cast("object", matter_id), uuid.UUID):
            msg = "matter_id must be a UUID"
            raise TypeError(msg)
        try:
            return self._matters[matter_id]
        except KeyError as exc:
            msg = f"Matter {matter_id} not found"
            raise KeyError(msg) from exc

    def reset(self) -> None:
        """Clear state (test helper)."""
        self._matters.clear()

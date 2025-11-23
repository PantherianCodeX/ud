# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Unit tests for matters service."""

from uuid import uuid4

import pytest

from udocket_api.workflow.matters.schemas import MatterCreateRequest
from udocket_api.workflow.matters.service import MattersService


def _payload(title: str) -> MatterCreateRequest:
    return MatterCreateRequest(
        title=title,
        description="Description",
        matter_type="general",
    )


def test_create_stores_matter() -> None:
    """Creating a matter stores it internally."""
    service = MattersService()
    matter = service.create(_payload("Test matter"))

    assert matter.id in {item.id for item in service.list()}


def test_get_missing_matter_raises() -> None:
    """Fetching a missing matter raises KeyError."""
    service = MattersService()
    with pytest.raises(KeyError):
        service.get(uuid4())

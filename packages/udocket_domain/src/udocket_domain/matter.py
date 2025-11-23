# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Matter-related domain models."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from .base import BaseEntity

MatterStatus = Literal["intake", "analysis", "review", "completed", "archived"]
PartyRole = Literal["client", "opposing_party", "witness", "attorney", "other"]


class Party(BaseEntity):
    """A person or organization involved in a legal matter.

    Represents clients, opposing parties, witnesses, attorneys, or
    other participants with their contact details and notes.

    Attributes:
        name: Full legal name of the party.
        role: Role of the party in the matter.
        contact_info: Optional contact details.
        notes: Additional notes about the party.
    """

    name: str = Field(..., min_length=1, max_length=255, description="Full name of the party")
    role: PartyRole = Field(..., description="Role of the party in the matter")
    contact_info: str | None = Field(None, max_length=500, description="Contact information")
    notes: str | None = Field(None, description="Additional notes about the party")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "John Doe",
                "role": "client",
                "contact_info": "john.doe@example.com",
                "notes": "Primary contact for case",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Relationship(BaseEntity):
    """Relationship between two parties in a matter.

    Represents directed connections between parties such as spouse,
    employer, or attorney relationships.

    Attributes:
        from_party_id: Source party identifier.
        to_party_id: Target party identifier.
        relationship_type: Type of relationship (e.g., spouse, employer).
        description: Optional description of the relationship.
    """

    from_party_id: UUID = Field(..., description="Source party ID")
    to_party_id: UUID = Field(..., description="Target party ID")
    relationship_type: str = Field(..., min_length=1, max_length=100, description="Type of relationship")
    description: str | None = Field(None, description="Description of the relationship")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "from_party_id": "550e8400-e29b-41d4-a716-446655440001",
                "to_party_id": "550e8400-e29b-41d4-a716-446655440003",
                "relationship_type": "spouse",
                "description": "Married for 10 years",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Matter(BaseEntity):
    """A legal matter or case.

    Central domain entity representing a legal case with its status,
    classification, and primary client association.

    Attributes:
        title: Display title for the matter.
        description: Optional detailed description.
        status: Current workflow status of the matter.
        matter_type: Classification of legal matter type.
        client_id: UUID of the primary client party.
    """

    title: str = Field(..., min_length=1, max_length=255, description="Matter title")
    description: str | None = Field(None, description="Detailed description of the matter")
    status: MatterStatus = Field(default="intake", description="Current status of the matter")
    matter_type: str = Field(..., min_length=1, max_length=100, description="Type of legal matter")
    client_id: UUID | None = Field(None, description="Primary client party ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Doe v. Smith Divorce",
                "description": "Divorce proceedings between John and Jane",
                "status": "intake",
                "matter_type": "family_law",
                "client_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }

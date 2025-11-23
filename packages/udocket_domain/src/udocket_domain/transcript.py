# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Transcript-related domain models."""

from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class SpeakerTurn(BaseEntity):
    """A single speaker turn in a transcript."""

    transcript_id: UUID = Field(..., description="Associated transcript ID")
    speaker_id: str = Field(..., min_length=1, max_length=100, description="Speaker identifier")
    speaker_name: str | None = Field(None, max_length=255, description="Speaker name (if known)")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., min_length=1, description="Transcribed text for this turn")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Transcription confidence score")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440030",
                "transcript_id": "550e8400-e29b-41d4-a716-446655440031",
                "speaker_id": "speaker_1",
                "speaker_name": "John Doe",
                "start_time": 0.0,
                "end_time": 5.5,
                "text": "I need help with my divorce case.",
                "confidence": 0.95,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Transcript(BaseEntity):
    """A complete transcript of a legal interview or consultation."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    audio_url: str | None = Field(None, max_length=500, description="URL to source audio file")
    language: str = Field(default="en", max_length=10, description="Language code (ISO 639-1)")
    duration_seconds: float | None = Field(None, ge=0, description="Audio duration in seconds")
    word_count: int | None = Field(None, ge=0, description="Total word count")
    transcription_service: str | None = Field(None, max_length=100, description="Service used for transcription")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440031",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "audio_url": "s3://bucket/audio/interview-123.wav",
                "language": "en",
                "duration_seconds": 3600.0,
                "word_count": 5000,
                "transcription_service": "azure_speech",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }

# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Analysis workflow service."""

from __future__ import annotations

from statistics import mean
from typing import cast
from uuid import UUID

from udocket_api.workflow.analysis.schemas import AnalysisRequest
from udocket_domain import MatterAnalysis


class AnalysisService:
    """Stateless analysis engine using heuristics for demo purposes."""

    def __init__(self) -> None:
        """Initialize service cache."""
        self._analyses: dict[UUID, MatterAnalysis] = {}

    def run_analysis(self, payload: AnalysisRequest) -> MatterAnalysis:
        """Generate a deterministic analysis summary.

        Args:
            payload: Validated analysis request received from the API layer.

        Returns:
            MatterAnalysis: Generated analysis artifact stored in memory.

        Raises:
            TypeError: If the payload is not a valid ``AnalysisRequest``.
        """
        if not isinstance(cast("object", payload), AnalysisRequest):
            msg = "payload must be an AnalysisRequest"
            raise TypeError(msg)
        summary = payload.transcript.strip().split(".")[0][:500]
        embedding = self._build_embedding(summary)
        analysis = MatterAnalysis(
            matter_id=payload.matter_id,
            summary=summary or "No transcript summary available.",
            embedding=embedding,
        )
        self._analyses[payload.matter_id] = analysis
        return analysis

    def get_analysis(self, matter_id: UUID) -> MatterAnalysis:
        """Return a cached analysis.

        Args:
            matter_id: Identifier for the matter whose analysis is requested.

        Returns:
            MatterAnalysis: Cached analysis associated with ``matter_id``.

        Raises:
            KeyError: If the analysis is missing.
            TypeError: If the identifier is not a ``UUID``.
        """
        if not isinstance(cast("object", matter_id), UUID):
            msg = "matter_id must be a UUID"
            raise TypeError(msg)
        try:
            return self._analyses[matter_id]
        except KeyError as exc:
            msg = f"No analysis found for matter {matter_id}"
            raise KeyError(msg) from exc

    @staticmethod
    def _build_embedding(summary: str) -> list[float]:
        """Compute a stable pseudo-embedding for demonstration.

        Args:
            summary: Summary text extracted from the matter transcript.

        Returns:
            list[float]: Averaged ASCII segments representing the summary.
        """
        if not (ascii_values := [float(ord(char)) for char in summary]):
            return []
        chunk_size = max(1, len(ascii_values) // 8)
        return [mean(ascii_values[i : i + chunk_size]) for i in range(0, len(ascii_values), chunk_size)]

    def reset(self) -> None:
        """Clear cached analyses."""
        self._analyses.clear()

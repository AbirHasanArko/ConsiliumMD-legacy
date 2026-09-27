"""CARMA adapter — Phase 2 placeholder.

Returns a graceful `ESCALATE` response until CARMA exposes a live service.
The shape is exactly what CARMA's `CARMAResponse` will produce, so swapping
the body of `reason()` for real CARMA calls is a Phase 2 task that does
not change the rest of the system.
"""
from __future__ import annotations

import time

from app.services.reasoning.provider import (
    ReasoningRequest,
    ReasoningResponse,
)
from app.services.reasoning.states import ConflictTypeLabel, RoutingDecision


class CARMAReasoningAdapter:
    name = "carma"

    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        started = time.perf_counter()
        # Until CARMA is wired, return a safe "Under Review" response. This
        # is intentional: the spec says never silent-fallback to the mock.
        return ReasoningResponse(
            routing=RoutingDecision.ESCALATE,
            conflict_label=ConflictTypeLabel.UNDER_REVIEW,
            recommendation_text=(
                "Reasoning engine (CARMA) is not yet connected. This case "
                "is being routed to senior clinical review."
            ),
            primary_evidence_grade="low",
            confidence=0.0,
            uncertainty_decomposition={"insufficient": 1.0},
            escalation_reason="reasoning_engine_unavailable",
            identifiability_flag=None,
            reasoning_trail=[
                {"step": "carma_unavailable", "detail": "Phase 2 not active"}
            ],
            model_version_name="carma-pending",
            latency_ms=(time.perf_counter() - started) * 1000,
        )

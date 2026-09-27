"""Single source of truth for routing decision <-> conflict label <-> UI state."""
from __future__ import annotations

from enum import Enum


class RoutingDecision(str, Enum):
    ANSWER = "answer"
    RETRIEVE = "retrieve"
    ELICIT = "elicit"
    ESCALATE = "escalate"


class ConflictTypeLabel(str, Enum):
    EVIDENCE_GAP_RESOLVED = "evidence_gap_resolved"
    EVIDENCE_GAP_CHECKING = "evidence_gap_checking"
    JUDGMENT_CALL = "judgment_call"
    UNDER_REVIEW = "under_review"


# Routing decision -> conflict label shown to the clinician.
CONFLICT_LABEL_FOR_ROUTING: dict[RoutingDecision, ConflictTypeLabel] = {
    RoutingDecision.ANSWER: ConflictTypeLabel.EVIDENCE_GAP_RESOLVED,
    RoutingDecision.RETRIEVE: ConflictTypeLabel.EVIDENCE_GAP_CHECKING,
    RoutingDecision.ELICIT: ConflictTypeLabel.JUDGMENT_CALL,
    RoutingDecision.ESCALATE: ConflictTypeLabel.UNDER_REVIEW,
}

# Routing decision -> initial recommendation row state. The state machine
# in `app/services/recommendation_lifecycle.py` is the only other place
# that knows about these strings.
TERMINAL_STATE_FOR_ROUTING: dict[RoutingDecision, str] = {
    RoutingDecision.ANSWER: "answered",
    RoutingDecision.RETRIEVE: "retrieved",
    RoutingDecision.ELICIT: "elicit_pending",
    RoutingDecision.ESCALATE: "escalated",
}


def routing_from_str(value: str) -> RoutingDecision:
    try:
        return RoutingDecision(value)
    except ValueError as exc:
        raise ValueError(f"unknown_routing_decision:{value}") from exc

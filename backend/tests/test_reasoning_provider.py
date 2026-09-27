"""Tests for the mock reasoning provider."""
from __future__ import annotations

from uuid import UUID

from app.services.reasoning.mock_provider import MockReasoningProvider
from app.services.reasoning.provider import PatientContext, ReasoningRequest
from app.services.reasoning.states import (
    ConflictTypeLabel,
    RoutingDecision,
)


def _req(case_id: str) -> ReasoningRequest:
    return ReasoningRequest(
        case_id=UUID(case_id),
        decision_class="any",
        patient_context=PatientContext(),
    )


def test_answer_routing():
    p = MockReasoningProvider()
    r = p.reason(_req("00000000-0000-0000-0000-000000000001"))  # Margaret Chen
    assert r.routing == RoutingDecision.ANSWER
    assert r.conflict_label == ConflictTypeLabel.EVIDENCE_GAP_RESOLVED
    assert r.safety_verdict in ("pass", "caution", "fail")


def test_retrieve_then_answer_routing():
    p = MockReasoningProvider()
    r1 = p.reason(_req("00000000-0000-0000-0000-000000000002"))  # James O'Brien
    assert r1.routing == RoutingDecision.RETRIEVE
    assert r1.conflict_label == ConflictTypeLabel.EVIDENCE_GAP_CHECKING

    # Re-evaluate with prior snapshot id -> answer.
    r2 = p.reason(
        ReasoningRequest(
            case_id=UUID("00000000-0000-0000-0000-000000000002"),
            decision_class="any",
            patient_context=PatientContext(),
            prior_snapshot_id=UUID("00000000-0000-0000-0000-000000000099"),
        )
    )
    assert r2.routing == RoutingDecision.ANSWER


def test_elicit_routing_has_options_and_tradeoff():
    p = MockReasoningProvider()
    r = p.reason(_req("00000000-0000-0000-0000-000000000003"))  # Priya Raman
    assert r.routing == RoutingDecision.ELICIT
    assert r.conflict_label == ConflictTypeLabel.JUDGMENT_CALL
    assert r.tradeoff_statement
    assert len(r.elicit_options) >= 2


def test_escalate_routing_has_reason():
    p = MockReasoningProvider()
    r = p.reason(_req("00000000-0000-0000-0000-000000000004"))  # Ahmed Al-Sayed
    assert r.routing == RoutingDecision.ESCALATE
    assert r.conflict_label == ConflictTypeLabel.UNDER_REVIEW
    assert r.escalation_reason
    assert r.identifiability_flag is False


def test_unknown_case_id_returns_answer_with_low_confidence():
    p = MockReasoningProvider()
    r = p.reason(_req("11111111-1111-1111-1111-111111111111"))
    assert r.routing == RoutingDecision.ANSWER
    assert r.confidence < 0.5

"""Recommendation lifecycle — creates snapshots, drives the state machine.

This module is the only place that mutates `recommendations.state` and
appends `reasoning_snapshots`. Every action is paired with one
`action_logs` row, and (optionally) one `audit_events` row, all in the
same DB transaction.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    ActionLog,
    AuditEvent,
    ClinicalCase,
    EvidenceCitation,
    ModelVersion,
    PatientAllergy,
    PatientMedication,
    Recommendation,
    ReasoningSnapshot,
    User,
)
from app.services.audit import AuditService
from app.services.reasoning import (
    RoutingDecision,
    get_reasoning_provider,
)
from app.services.reasoning.provider import (
    PatientContext,
    ReasoningRequest,
    ReasoningResponse,
)
from app.services.reasoning.states import (
    CONFLICT_LABEL_FOR_ROUTING,
    TERMINAL_STATE_FOR_ROUTING,
)
from app.services.safety_auditor import audit_recommendation


# Allowed transitions out of each state.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"answered", "retrieved", "elicit_pending", "escalated"},
    "retrieved": {"answered"},
    "answered": {"accepted", "overridden", "escalated", "elicit_pending"},
    "elicit_pending": {"answered"},
    "escalated": {"under_review"},
    "under_review": {"resolved"},
    "accepted": set(),
    "overridden": set(),
    "resolved": set(),
}


# Action names that gate "recommendation:action" permission.
ACTION_VERBS = {"accept", "request_evidence", "override"}


def transition(recommendation: Recommendation, target: str) -> None:
    current = recommendation.state
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"invalid_state_transition:{current}->{target}"
            ),
        )
    recommendation.state = target


def _ensure_model_version(db: Session, name: str) -> ModelVersion:
    mv = db.query(ModelVersion).filter_by(name=name).first()
    if mv is not None:
        return mv
    mv = ModelVersion(provider=name.split("-")[0], name=name, is_active=True)
    db.add(mv)
    db.flush()
    return mv


def _patient_context_from_case(case: ClinicalCase) -> PatientContext:
    p = case.patient
    demographics = p.demographics
    conditions = [c.label for c in p.conditions if c.label]
    meds = [m.label for m in p.medications if m.label]
    allergies = [a.substance for a in p.allergies if a.substance]

    vital_signs: dict[str, Any] = {}
    lab_values: dict[str, Any] = {}
    # Use the most recent vital sign if any.
    if p.vitals:
        latest = max(p.vitals, key=lambda v: v.recorded_at)
        if latest.systolic_bp is not None:
            vital_signs["systolic_bp"] = latest.systolic_bp
        if latest.diastolic_bp is not None:
            vital_signs["diastolic_bp"] = latest.diastolic_bp
        if latest.hr is not None:
            vital_signs["hr"] = latest.hr
        if latest.spo2 is not None:
            vital_signs["spo2"] = latest.spo2
        if latest.glucose_mg_dl is not None:
            lab_values["glucose"] = latest.glucose_mg_dl
    return PatientContext(
        age=None,
        sex=demographics.sex if demographics else None,
        conditions=conditions,
        medications=meds,
        allergies=allergies,
        vital_signs=vital_signs,
        lab_values=lab_values,
    )


def _ensure_only_one_open(db: Session, case: ClinicalCase) -> None:
    """Cases may only have one open (non-terminal) recommendation at a time."""
    open_states = {"pending", "retrieved", "answered", "elicit_pending", "escalated"}
    existing = (
        db.query(Recommendation)
        .filter(
            Recommendation.case_id == case.id,
            Recommendation.state.in_(open_states),
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"recommendation_already_open:{existing.id}",
        )


def create_recommendation(
    db: Session,
    *,
    case: ClinicalCase,
    actor: User | None,
    ip: str | None,
    user_agent: str | None,
    elicit_response: dict[str, Any] | None = None,
    prior_snapshot_id: UUID | None = None,
) -> tuple[Recommendation, ReasoningSnapshot]:
    """Create a recommendation: call provider, persist snapshot, write audit event."""
    if case.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="case_closed",
        )
    _ensure_only_one_open(db, case)

    provider = get_reasoning_provider()
    request = ReasoningRequest(
        case_id=case.id,
        decision_class=case.decision_class,
        patient_context=_patient_context_from_case(case),
        prior_snapshot_id=prior_snapshot_id,
        elicit_response=elicit_response,
    )

    # Local safety rule-check against patient's own record.
    safety = audit_recommendation(
        recommendation_text="",  # pre-text; will re-check below
        allergies=[a.substance for a in case.patient.allergies],
        active_medications=[
            m.label for m in case.patient.medications if m.stopped_at is None
        ],
    )

    response: ReasoningResponse = provider.reason(request)

    # Re-run safety auditor against the actual recommendation text now that
    # we have it.
    safety = audit_recommendation(
        recommendation_text=response.recommendation_text,
        allergies=[a.substance for a in case.patient.allergies],
        active_medications=[
            m.label for m in case.patient.medications if m.stopped_at is None
        ],
    )
    response.safety_verdict = safety.verdict
    response.safety_issues = list(safety.issues)

    mv = _ensure_model_version(db, response.model_version_name)

    initial_state = TERMINAL_STATE_FOR_ROUTING[response.routing]
    # Special case: an ELICIT response re-eval produces ANSWER state directly.
    if elicit_response is not None and response.routing == RoutingDecision.ANSWER:
        initial_state = "answered"

    seq = 0
    if prior_snapshot_id is not None:
        prior = db.get(ReasoningSnapshot, prior_snapshot_id)
        if prior is not None:
            seq = prior.sequence_number + 1

    snapshot = ReasoningSnapshot(
        recommendation_id=None,  # set after we create the recommendation row
        model_version_id=mv.id,
        routing_decision=response.routing.value,
        conflict_label=response.conflict_label.value,
        recommendation_text=response.recommendation_text,
        confidence=response.confidence,
        tradeoff_statement=response.tradeoff_statement,
        elicit_question=response.elicit_question,
        elicit_options_json=json.dumps(
            [o.model_dump() for o in response.elicit_options]
        ) if response.elicit_options else None,
        escalation_reason=response.escalation_reason,
        identifiability_flag=response.identifiability_flag or False,
        uncertainty_json=json.dumps(response.uncertainty_decomposition),
        safety_verdict=response.safety_verdict,
        safety_issues_json=json.dumps(response.safety_issues),
        reasoning_trail_json=json.dumps(
            [s.model_dump() for s in response.reasoning_trail]
        ),
        latency_ms=response.latency_ms,
        sequence_number=seq,
        primary_evidence_grade=response.primary_evidence_grade,
    )

    rec = Recommendation(
        case_id=case.id,
        state=initial_state,
    )
    db.add(rec)
    db.flush()  # assigns rec.id

    snapshot.recommendation_id = rec.id
    db.add(snapshot)
    db.flush()  # assigns snapshot.id

    rec.latest_snapshot_id = snapshot.id
    db.add(rec)

    # Persist evidence citations.
    for c in response.evidence_citations:
        db.add(
            EvidenceCitation(
                snapshot_id=snapshot.id,
                external_passage_id=c.external_passage_id,
                source_body=c.source_body,
                document_title=c.document_title,
                section=c.section,
                evidence_grade=c.evidence_grade,
                study_design=c.study_design,
                relevance_score=c.relevance_score,
                quality_score=c.quality_score,
                excerpt=c.excerpt,
            )
        )

    db.add(
        ActionLog(
            recommendation_id=rec.id,
            actor_user_id=actor.id if actor else None,
            action="recommendation.create",
            payload_json=json.dumps(
                {
                    "routing": response.routing.value,
                    "snapshot_sequence": seq,
                }
            ),
        )
    )

    audit = AuditService(db)
    audit.record(
        action="recommendation.create",
        target_type="recommendation",
        target_id=rec.id,
        actor_user_id=actor.id if actor else None,
        ip=ip,
        user_agent=user_agent,
        payload={
            "case_id": str(case.id),
            "routing": response.routing.value,
            "safety_verdict": response.safety_verdict,
            "model_version": response.model_version_name,
        },
    )

    if response.safety_verdict in ("caution", "fail"):
        audit.record(
            action="recommendation.safety_flag",
            target_type="recommendation",
            target_id=rec.id,
            actor_user_id=actor.id if actor else None,
            ip=ip,
            user_agent=user_agent,
            payload={"verdict": response.safety_verdict, "issues": response.safety_issues},
        )

    return rec, snapshot


def perform_action(
    db: Session,
    *,
    recommendation: Recommendation,
    actor: User,
    action: str,
    rationale: str | None,
    ip: str | None,
    user_agent: str | None,
    elicit_response: dict[str, Any] | None = None,
    payload_extra: dict[str, Any] | None = None,
) -> Recommendation:
    """Apply a doctor action to a recommendation. Encapsulates the state machine."""
    verb_to_target: dict[str, str] = {
        "accept": "accepted",
        "override": "overridden",
        "escalate": "escalated",
        "request_evidence": "retrieved",
        "resolve": "resolved",
    }
    target = verb_to_target[action]

    transition(recommendation, target)


def transition_or_skip_if_same(recommendation: Recommendation, target: str) -> None:
    """Allow re-issuing the same transition (e.g. request_evidence from
    an already-retrieved state) without raising 409."""
    if recommendation.state == target:
        return
    transition(recommendation, target)

    if action == "override":
        if not rationale or not rationale.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="missing_rationale",
            )
        recommendation.final_rationale = rationale.strip()
        # Pull the recommendation text from the latest snapshot via direct query.
        latest = (
            db.query(ReasoningSnapshot)
            .filter(ReasoningSnapshot.recommendation_id == recommendation.id)
            .order_by(ReasoningSnapshot.sequence_number.desc())
            .first()
        )
        recommendation.final_recommendation_text = (
            latest.recommendation_text if latest else None
        )

    if action == "accept":
        latest = (
            db.query(ReasoningSnapshot)
            .filter(ReasoningSnapshot.recommendation_id == recommendation.id)
            .order_by(ReasoningSnapshot.sequence_number.desc())
            .first()
        )
        recommendation.final_recommendation_text = (
            latest.recommendation_text if latest else None
        )

    db.add(
        ActionLog(
            recommendation_id=recommendation.id,
            actor_user_id=actor.id,
            action=f"recommendation.{action}",
            rationale=rationale,
            payload_json=json.dumps(payload_extra or {}),
        )
    )

    audit = AuditService(db)
    audit.record(
        action=f"recommendation.{action}",
        target_type="recommendation",
        target_id=recommendation.id,
        actor_user_id=actor.id,
        ip=ip,
        user_agent=user_agent,
        payload={"rationale": rationale, **(payload_extra or {})},
    )
    return recommendation


def mark_decision(recommendation: Recommendation) -> None:
    from datetime import datetime

    recommendation.decided_at = datetime.utcnow()


def _append_followup_snapshot(
    db: Session,
    *,
    recommendation: Recommendation,
    case: ClinicalCase,
    actor: User,
    ip: str | None,
    user_agent: str | None,
    elicit_response: dict[str, Any] | None = None,
) -> ReasoningSnapshot:
    """Append a follow-up snapshot to an existing recommendation.

    Used by `request-evidence` and `elicit-response` — instead of creating
    a new recommendation row, we add another snapshot to the same row and
    point `latest_snapshot_id` at it.
    """
    provider = get_reasoning_provider()
    request = ReasoningRequest(
        case_id=case.id,
        decision_class=case.decision_class,
        patient_context=_patient_context_from_case(case),
        prior_snapshot_id=recommendation.latest_snapshot_id,
        elicit_response=elicit_response,
    )
    response: ReasoningResponse = provider.reason(request)

    safety = audit_recommendation(
        recommendation_text=response.recommendation_text,
        allergies=[a.substance for a in case.patient.allergies],
        active_medications=[
            m.label
            for m in case.patient.medications
            if m.stopped_at is None
        ],
    )
    response.safety_verdict = safety.verdict
    response.safety_issues = list(safety.issues)

    mv = _ensure_model_version(db, response.model_version_name)

    # ELICIT follow-up keeps the rec in elicit_pending until a preference
    # is submitted; an ELICIT follow-up with elicit_response set advances
    # to answered.
    if request.elicit_response is not None and response.routing == RoutingDecision.ANSWER:
        recommendation.state = "answered"
    elif response.routing == RoutingDecision.ELICIT:
        recommendation.state = "elicit_pending"
    else:
        # ANSWER after retrieval -> rec becomes 'answered'.
        recommendation.state = TERMINAL_STATE_FOR_ROUTING[response.routing]

    seq = 0
    if recommendation.latest_snapshot_id:
        prior = db.get(ReasoningSnapshot, recommendation.latest_snapshot_id)
        if prior is not None:
            seq = prior.sequence_number + 1

    snap = ReasoningSnapshot(
        recommendation_id=recommendation.id,
        model_version_id=mv.id,
        routing_decision=response.routing.value,
        conflict_label=response.conflict_label.value,
        recommendation_text=response.recommendation_text,
        confidence=response.confidence,
        tradeoff_statement=response.tradeoff_statement,
        elicit_question=response.elicit_question,
        elicit_options_json=json.dumps(
            [o.model_dump() for o in response.elicit_options]
        ) if response.elicit_options else None,
        escalation_reason=response.escalation_reason,
        identifiability_flag=response.identifiability_flag or False,
        uncertainty_json=json.dumps(response.uncertainty_decomposition),
        safety_verdict=response.safety_verdict,
        safety_issues_json=json.dumps(response.safety_issues),
        reasoning_trail_json=json.dumps(
            [s.model_dump() for s in response.reasoning_trail]
        ),
        latency_ms=response.latency_ms,
        sequence_number=seq,
        primary_evidence_grade=response.primary_evidence_grade,
    )
    db.add(snap)
    db.flush()
    recommendation.latest_snapshot_id = snap.id

    db.add(
        ActionLog(
            recommendation_id=recommendation.id,
            actor_user_id=actor.id if actor else None,
            action="recommendation.snapshot_added",
            payload_json=json.dumps(
                {"routing": response.routing.value, "snapshot_sequence": seq}
            ),
        )
    )
    AuditService(db).record(
        action="recommendation.snapshot_added",
        target_type="recommendation",
        target_id=recommendation.id,
        actor_user_id=actor.id if actor else None,
        ip=ip,
        user_agent=user_agent,
        payload={
            "routing": response.routing.value,
            "safety_verdict": response.safety_verdict,
            "model_version": response.model_version_name,
        },
    )
    if response.safety_verdict in ("caution", "fail"):
        AuditService(db).record(
            action="recommendation.safety_flag",
            target_type="recommendation",
            target_id=recommendation.id,
            actor_user_id=actor.id if actor else None,
            ip=ip,
            user_agent=user_agent,
            payload={
                "verdict": response.safety_verdict,
                "issues": response.safety_issues,
            },
        )
    return snap

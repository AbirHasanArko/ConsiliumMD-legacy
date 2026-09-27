"""Recommendation + action router."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rbac import (
    PERM_RECOMMENDATION_ACTION,
    PERM_RECOMMENDATION_VIEW,
    ROLE_DOCTOR,
    ROLE_SENIOR_CLINICIAN,
)
from app.deps import db_dep, require_permission, require_role
from app.models import ClinicalCase, Recommendation, ReasoningSnapshot, User
from app.schemas.recommendation import (
    ActionResponse,
    ElicitRequest,
    EscalateRequest,
    EvidenceCitationResponse,
    OverrideRequest,
    RecommendationListItem,
    RecommendationResponse,
    RequestEvidenceResponse,
)
from app.services.audit import AuditService, client_ip
from app.services.recommendation_lifecycle import (
    create_recommendation,
    mark_decision,
    perform_action,
)

router = APIRouter(tags=["recommendations"])


def _serialize(rec: Recommendation) -> RecommendationResponse:
    # We dropped the bidirectional relationship to avoid the
    # recommendation_id <-> latest_snapshot_id FK cycle. The latest snapshot
    # is loaded explicitly when needed.
    from sqlalchemy.orm.attributes import instance_state

    state = instance_state(rec)
    session = state.session if state is not None else None

    snap: ReasoningSnapshot | None = None
    if rec.latest_snapshot_id and session is not None:
        snap = session.get(ReasoningSnapshot, rec.latest_snapshot_id)
    snapshot_dict: dict[str, Any] | None = None
    citations: list[EvidenceCitationResponse] = []
    if snap is not None:
        snapshot_dict = {
            "id": str(snap.id),
            "model_version": snap.model_version.name if snap.model_version else "",
            "routing_decision": snap.routing_decision,
            "conflict_label": snap.conflict_label,
            "recommendation_text": snap.recommendation_text,
            "primary_evidence_grade": snap.primary_evidence_grade,
            "confidence": snap.confidence,
            "tradeoff_statement": snap.tradeoff_statement,
            "elicit_question": snap.elicit_question,
            "elicit_options": json.loads(snap.elicit_options_json) if snap.elicit_options_json else [],
            "escalation_reason": snap.escalation_reason,
            "identifiability_flag": snap.identifiability_flag,
            "uncertainty_decomposition": json.loads(snap.uncertainty_json),
            "safety_verdict": snap.safety_verdict,
            "safety_issues": json.loads(snap.safety_issues_json),
            "reasoning_trail": json.loads(snap.reasoning_trail_json),
            "latency_ms": snap.latency_ms,
            "sequence_number": snap.sequence_number,
            "created_at": snap.created_at.isoformat(),
        }
        citations = [
            EvidenceCitationResponse(
                id=c.id,
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
            for c in snap.evidence_citations
        ]
    return RecommendationResponse(
        id=rec.id,
        case_id=rec.case_id,
        state=rec.state,
        final_recommendation_text=rec.final_recommendation_text,
        final_rationale=rec.final_rationale,
        decided_at=rec.decided_at,
        created_at=rec.created_at,
        latest_snapshot_id=rec.latest_snapshot_id,
        snapshot=snapshot_dict,
        citations=citations,
    )


@router.get("/cases/{case_id}/recommendations", response_model=list[RecommendationListItem])
def list_case_recommendations(
    case_id: UUID,
    db: Session = Depends(db_dep),
    _u: User = Depends(require_permission(PERM_RECOMMENDATION_VIEW)),
) -> list[RecommendationListItem]:
    case = db.get(ClinicalCase, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case_not_found")
    return [
        RecommendationListItem(
            id=r.id,
            case_id=r.case_id,
            state=r.state,
            created_at=r.created_at,
            decided_at=r.decided_at,
        )
        for r in sorted(case.recommendations, key=lambda r: r.created_at)
    ]


@router.post(
    "/cases/{case_id}/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation_endpoint(
    case_id: UUID,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_RECOMMENDATION_ACTION)),
) -> RecommendationResponse:
    case = db.get(ClinicalCase, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case_not_found")
    rec, _snap = create_recommendation(
        db,
        case=case,
        actor=actor,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(rec)
    return _serialize(rec)


@router.get("/recommendations/{rec_id}", response_model=RecommendationResponse)
def get_recommendation(
    rec_id: UUID,
    db: Session = Depends(db_dep),
    _u: User = Depends(require_permission(PERM_RECOMMENDATION_VIEW)),
) -> RecommendationResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    return _serialize(rec)


@router.get(
    "/recommendations/{rec_id}/reasoning-trail",
    response_model=RecommendationResponse,
)
def get_reasoning_trail(
    rec_id: UUID,
    db: Session = Depends(db_dep),
    _u: User = Depends(require_permission(PERM_RECOMMENDATION_VIEW)),
) -> RecommendationResponse:
    return get_recommendation(rec_id, db, _u)


@router.post("/recommendations/{rec_id}/accept", response_model=ActionResponse)
def accept_recommendation(
    rec_id: UUID,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_RECOMMENDATION_ACTION)),
) -> ActionResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    perform_action(
        db,
        recommendation=rec,
        actor=actor,
        action="accept",
        rationale=None,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    mark_decision(rec)
    db.commit()
    db.refresh(rec)
    return ActionResponse(
        recommendation_id=rec.id,
        state=rec.state,
        decided_at=rec.decided_at,
        final_recommendation_text=rec.final_recommendation_text,
        final_rationale=rec.final_rationale,
    )


@router.post(
    "/recommendations/{rec_id}/request-evidence",
    response_model=RequestEvidenceResponse,
)
def request_evidence(
    rec_id: UUID,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_RECOMMENDATION_ACTION)),
) -> RequestEvidenceResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    case = db.get(ClinicalCase, rec.case_id)

    # Transition the existing recommendation to "retrieved" (records the
    # action + audit), then call the provider again with prior_snapshot_id
    # so it advances to ANSWER on this same recommendation. We append a new
    # reasoning_snapshot rather than creating a new recommendation row.
    from app.services.recommendation_lifecycle import transition_or_skip_if_same

    transition_or_skip_if_same(rec, "retrieved")
    db.add(
        __import__("app.models", fromlist=["ActionLog"]).ActionLog(
            recommendation_id=rec.id,
            actor_user_id=actor.id,
            action="recommendation.request_evidence",
            payload_json="{}",
        )
    )
    AuditService(db).record(
        action="recommendation.request_evidence",
        target_type="recommendation",
        target_id=rec.id,
        actor_user_id=actor.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload={},
    )
    db.flush()

    from app.services.recommendation_lifecycle import _append_followup_snapshot

    new_snap = _append_followup_snapshot(
        db,
        recommendation=rec,
        case=case,
        actor=actor,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(rec)
    return RequestEvidenceResponse(
        recommendation_id=rec.id,
        state=rec.state,
        snapshot_sequence=new_snap.sequence_number,
    )


@router.post("/recommendations/{rec_id}/escalate", response_model=ActionResponse)
def escalate_recommendation(
    rec_id: UUID,
    req: EscalateRequest,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_RECOMMENDATION_ACTION)),
) -> ActionResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    perform_action(
        db,
        recommendation=rec,
        actor=actor,
        action="escalate",
        rationale=req.note,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload_extra={"note": req.note} if req.note else None,
    )
    mark_decision(rec)
    db.commit()
    db.refresh(rec)
    return ActionResponse(
        recommendation_id=rec.id,
        state=rec.state,
        decided_at=rec.decided_at,
        final_recommendation_text=rec.final_recommendation_text,
        final_rationale=rec.final_rationale,
    )


@router.post("/recommendations/{rec_id}/override", response_model=ActionResponse)
def override_recommendation(
    rec_id: UUID,
    req: OverrideRequest,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_RECOMMENDATION_ACTION)),
) -> ActionResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    perform_action(
        db,
        recommendation=rec,
        actor=actor,
        action="override",
        rationale=req.rationale,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    mark_decision(rec)
    db.commit()
    db.refresh(rec)
    return ActionResponse(
        recommendation_id=rec.id,
        state=rec.state,
        decided_at=rec.decided_at,
        final_recommendation_text=rec.final_recommendation_text,
        final_rationale=rec.final_rationale,
    )


@router.post("/recommendations/{rec_id}/elicit", response_model=ActionResponse)
def elicit_response(
    rec_id: UUID,
    req: ElicitRequest,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_RECOMMENDATION_ACTION)),
) -> ActionResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    if rec.state != "elicit_pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"not_in_elicit_state:{rec.state}",
        )
    # Validate the selected option against the snapshot's options. The
    # rec-snapshot relationship is unidirectional; load the latest snapshot
    # directly via the session.
    if rec.latest_snapshot_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="no_snapshot_on_recommendation",
        )
    snap = db.get(ReasoningSnapshot, rec.latest_snapshot_id)
    options = json.loads(snap.elicit_options_json) if snap and snap.elicit_options_json else []
    valid_ids = {o["id"] for o in options}
    if req.selected_option_id not in valid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid_option_id:{req.selected_option_id}",
        )

    # Re-run the provider with elicit_response so it can produce ANSWER.
    # We append a new snapshot to the same recommendation rather than
    # creating a new row.
    case = db.get(ClinicalCase, rec.case_id)
    from app.services.recommendation_lifecycle import _append_followup_snapshot

    new_snap = _append_followup_snapshot(
        db,
        recommendation=rec,
        case=case,
        actor=actor,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        elicit_response={
            "selected_option_id": req.selected_option_id,
            "free_text_response": req.free_text_response,
        },
    )

    # Also persist the elicitation record.
    from app.models import Elicitation

    db.add(
        Elicitation(
            recommendation_id=rec.id,
            responder_user_id=actor.id,
            presented_options_json=snap.elicit_options_json or "[]",
            selected_option_id=req.selected_option_id,
            free_text_response=req.free_text_response,
        )
    )
    db.add(
        __import__("app.models", fromlist=["ActionLog"]).ActionLog(
            recommendation_id=rec.id,
            actor_user_id=actor.id,
            action="recommendation.elicit_submit",
            rationale=req.free_text_response,
            payload_json=json.dumps(
                {"selected_option_id": req.selected_option_id}
            ),
        )
    )
    AuditService(db).record(
        action="recommendation.elicit_submit",
        target_type="recommendation",
        target_id=rec.id,
        actor_user_id=actor.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload={"selected_option_id": req.selected_option_id},
    )
    db.commit()
    db.refresh(rec)
    return ActionResponse(
        recommendation_id=rec.id,
        state=rec.state,
        decided_at=rec.decided_at,
        final_recommendation_text=rec.final_recommendation_text,
        final_rationale=rec.final_rationale,
    )

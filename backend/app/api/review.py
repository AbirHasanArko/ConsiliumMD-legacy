"""Senior clinician review router."""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rbac import (
    PERM_RECOMMENDATION_REVIEW,
    ROLE_SENIOR_CLINICIAN,
)
from app.deps import db_dep, require_role
from app.models import ClinicalCase, Recommendation, User
from app.schemas.recommendation import (
    RecommendationListItem,
    RecommendationResponse,
    ResolveRequest,
)
from app.services.audit import AuditService, client_ip
from app.services.recommendation_lifecycle import (
    mark_decision,
    perform_action,
    transition,
)

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/queue", response_model=list[RecommendationListItem])
def list_queue(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_SENIOR_CLINICIAN)),
) -> list[RecommendationListItem]:
    """Recommendations in `escalated` or `under_review` state, oldest first."""
    rows = (
        db.query(Recommendation)
        .filter(Recommendation.state.in_(["escalated", "under_review"]))
        .order_by(Recommendation.created_at.asc())
        .all()
    )
    return [
        RecommendationListItem(
            id=r.id,
            case_id=r.case_id,
            state=r.state,
            created_at=r.created_at,
            decided_at=r.decided_at,
        )
        for r in rows
    ]


@router.post(
    "/{rec_id}/resolve",
    response_model=RecommendationResponse,
)
def resolve_recommendation(
    rec_id: UUID,
    req: ResolveRequest,
    request: Request,
    db: Session = Depends(db_dep),
    reviewer: User = Depends(require_role(ROLE_SENIOR_CLINICIAN)),
) -> RecommendationResponse:
    rec = db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="recommendation_not_found"
        )
    if rec.state not in ("escalated", "under_review"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"not_in_review_state:{rec.state}",
        )
    case = db.get(ClinicalCase, rec.case_id)
    # Advance to under_review first if currently escalated, so the resolve
    # transition is valid.
    if rec.state == "escalated":
        transition(rec, "under_review")

    perform_action(
        db,
        recommendation=rec,
        actor=reviewer,
        action="resolve",
        rationale=req.rationale,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload_extra={"final_recommendation_text": req.final_recommendation_text},
    )
    rec.final_recommendation_text = req.final_recommendation_text
    case.senior_reviewer_id = reviewer.id
    mark_decision(rec)
    db.commit()
    db.refresh(rec)

    # Re-serialize via the recommendations router helper.
    from app.api.recommendations import _serialize

    return _serialize(rec)

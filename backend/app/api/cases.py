"""Clinical case router + decision-class listing."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.rbac import (
    PERM_CASE_CREATE,
    ROLE_DOCTOR,
)
from app.deps import db_dep, require_permission, require_role
from app.models import ClinicalCase, DecisionClassScope, Patient, User
from app.schemas.case import (
    CaseCreateRequest,
    CaseListItem,
    CaseResponse,
    DecisionClassResponse,
)
from app.services.audit import AuditService, client_ip
from app.services.reasoning.mock_provider import load_seeded_decision_classes
from app.services.scope import assert_decision_class_in_scope, is_in_scope

router = APIRouter(prefix="/cases", tags=["cases"])
_decision_classes_router = APIRouter(prefix="/decision-classes", tags=["decision-classes"])


@router.get("", response_model=list[CaseListItem])
def list_cases(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_DOCTOR, "admin", "senior_clinician")),
) -> list[CaseListItem]:
    cases = db.query(ClinicalCase).order_by(ClinicalCase.created_at.desc()).all()
    return [
        CaseListItem(
            id=c.id,
            patient_id=c.patient_id,
            doctor_id=c.doctor_id,
            senior_reviewer_id=c.senior_reviewer_id,
            decision_class=c.decision_class,
            title=c.title,
            status=c.status,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    req: CaseCreateRequest,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_CASE_CREATE)),
) -> CaseResponse:
    patient = db.get(Patient, req.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient_not_found")
    assert_decision_class_in_scope(db, req.decision_class)
    case = ClinicalCase(
        patient_id=req.patient_id,
        doctor_id=actor.id,
        senior_reviewer_id=req.senior_reviewer_id,
        decision_class=req.decision_class,
        title=req.title,
    )
    db.add(case)
    db.flush()

    AuditService(db).record(
        action="case.create",
        target_type="case",
        target_id=case.id,
        actor_user_id=actor.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
        payload={
            "decision_class": req.decision_class,
            "patient_id": str(req.patient_id),
        },
    )
    db.commit()
    db.refresh(case)
    return CaseResponse(
        id=case.id,
        patient_id=case.patient_id,
        doctor_id=case.doctor_id,
        senior_reviewer_id=case.senior_reviewer_id,
        decision_class=case.decision_class,
        title=case.title,
        status=case.status,
        created_at=case.created_at,
        updated_at=case.updated_at,
        closed_at=case.closed_at,
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: UUID,
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_DOCTOR, "admin", "senior_clinician")),
) -> CaseResponse:
    case = db.get(ClinicalCase, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case_not_found")
    return CaseResponse(
        id=case.id,
        patient_id=case.patient_id,
        doctor_id=case.doctor_id,
        senior_reviewer_id=case.senior_reviewer_id,
        decision_class=case.decision_class,
        title=case.title,
        status=case.status,
        created_at=case.created_at,
        updated_at=case.updated_at,
        closed_at=case.closed_at,
    )


@_decision_classes_router.get("", response_model=list[DecisionClassResponse])
def list_decision_classes(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_DOCTOR, "admin", "senior_clinician")),
) -> list[DecisionClassResponse]:
    rows = db.query(DecisionClassScope).order_by(DecisionClassScope.display_label).all()
    # Always merge any seeded entries that haven't been persisted yet
    # (so newly-cloned environments don't need a separate seed for this).
    seeded = {c["decision_class"]: c for c in load_seeded_decision_classes()}
    out: list[DecisionClassResponse] = []
    for row in rows:
        out.append(
            DecisionClassResponse(
                decision_class=row.decision_class,
                display_label=row.display_label,
                in_scope=row.in_scope,
                requires_ethics_review=row.requires_ethics_review,
                notes=row.notes,
            )
        )
    for key, c in seeded.items():
        if key not in {r.decision_class for r in rows}:
            out.append(
                DecisionClassResponse(
                    decision_class=c["decision_class"],
                    display_label=c["display_label"],
                    in_scope=c.get("in_scope", True),
                    requires_ethics_review=c.get("requires_ethics_review", False),
                    notes=c.get("notes", ""),
                )
            )
    return out

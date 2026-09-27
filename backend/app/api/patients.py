"""Patient router."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.deps import db_dep, require_permission
from app.models import (
    AuditEvent,
    Patient,
    PatientAllergy,
    PatientCondition,
    PatientDemographics,
    PatientMedication,
    PatientVital,
    User,
)
from app.core.rbac import (
    PERM_CASE_CREATE,
    ROLE_DOCTOR,
)
from app.schemas.patient import (
    AllergyCreate,
    ConditionCreate,
    DemographicsPayload,
    MedicationCreate,
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListResponse,
    PatientSummaryResponse,
    VitalCreate,
)
from app.services.audit import AuditService, client_ip

router = APIRouter(prefix="/patients", tags=["patients"])


def _serialize(patient: Patient) -> PatientDetailResponse:
    demographics = (
        DemographicsPayload(
            dob=patient.demographics.dob,
            sex=patient.demographics.sex,
            ethnicity=patient.demographics.ethnicity,
        )
        if patient.demographics
        else DemographicsPayload()
    )
    return PatientDetailResponse(
        id=patient.id,
        display_name=patient.display_name,
        external_mrn=patient.external_mrn,
        demographics=demographics,
        conditions=[
            {
                "id": str(c.id),
                "icd10_code": c.icd10_code,
                "label": c.label,
                "onset_date": c.onset_date.isoformat() if c.onset_date else None,
                "status": c.status,
            }
            for c in patient.conditions
        ],
        medications=[
            {
                "id": str(m.id),
                "rxnorm_code": m.rxnorm_code,
                "label": m.label,
                "dose": m.dose,
                "started_at": m.started_at.isoformat() if m.started_at else None,
                "stopped_at": m.stopped_at.isoformat() if m.stopped_at else None,
            }
            for m in patient.medications
        ],
        allergies=[
            {
                "id": str(a.id),
                "substance": a.substance,
                "reaction": a.reaction,
                "severity": a.severity,
            }
            for a in patient.allergies
        ],
        vitals=[
            {
                "id": str(v.id),
                "recorded_at": v.recorded_at.isoformat(),
                "systolic_bp": v.systolic_bp,
                "diastolic_bp": v.diastolic_bp,
                "hr": v.hr,
                "spo2": v.spo2,
                "temp_c": v.temp_c,
                "glucose_mg_dl": v.glucose_mg_dl,
                "notes": v.notes,
            }
            for v in patient.vitals
        ],
        created_at=patient.created_at,
    )


@router.get("", response_model=PatientListResponse)
def list_patients(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_permission(PERM_CASE_CREATE)),
) -> PatientListResponse:
    patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
    return PatientListResponse(
        items=[
            PatientSummaryResponse(
                id=p.id,
                display_name=p.display_name,
                external_mrn=p.external_mrn,
                created_at=p.created_at,
            )
            for p in patients
        ],
        total=len(patients),
    )


@router.post("", response_model=PatientDetailResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    req: PatientCreateRequest,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_CASE_CREATE)),
) -> PatientDetailResponse:
    patient = Patient(
        display_name=req.display_name,
        external_mrn=req.external_mrn,
    )
    db.add(patient)
    db.flush()

    patient.demographics = PatientDemographics(
        patient_id=patient.id,
        dob=req.demographics.dob,
        sex=req.demographics.sex,
        ethnicity=req.demographics.ethnicity,
    )
    for c in req.conditions:
        db.add(PatientCondition(patient_id=patient.id, **c.model_dump()))
    for m in req.medications:
        db.add(PatientMedication(patient_id=patient.id, **m.model_dump()))
    for a in req.allergies:
        db.add(PatientAllergy(patient_id=patient.id, **a.model_dump()))
    for v in req.vitals:
        db.add(PatientVital(patient_id=patient.id, **v.model_dump()))

    AuditService(db).record(
        action="patient.create",
        target_type="patient",
        target_id=patient.id,
        actor_user_id=actor.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(patient)
    return _serialize(patient)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(db_dep),
    _u: User = Depends(require_permission(PERM_CASE_CREATE)),
) -> PatientDetailResponse:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient_not_found")
    return _serialize(patient)


@router.post("/{patient_id}/vitals", response_model=PatientDetailResponse)
def add_vital(
    patient_id: UUID,
    req: VitalCreate,
    request: Request,
    db: Session = Depends(db_dep),
    actor: User = Depends(require_permission(PERM_CASE_CREATE)),
) -> PatientDetailResponse:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient_not_found")
    db.add(PatientVital(patient_id=patient.id, **req.model_dump()))
    AuditService(db).record(
        action="patient.vitals_add",
        target_type="patient",
        target_id=patient.id,
        actor_user_id=actor.id,
        ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(patient)
    return _serialize(patient)

"""Clinical case schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CaseCreateRequest(BaseModel):
    patient_id: UUID
    decision_class: str
    title: str
    senior_reviewer_id: UUID | None = None


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    doctor_id: UUID
    senior_reviewer_id: UUID | None
    decision_class: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    doctor_id: UUID
    senior_reviewer_id: UUID | None
    decision_class: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class DecisionClassResponse(BaseModel):
    decision_class: str
    display_label: str
    in_scope: bool
    requires_ethics_review: bool
    notes: str = ""

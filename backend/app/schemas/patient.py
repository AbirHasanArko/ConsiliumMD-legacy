"""Patient schemas."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConditionCreate(BaseModel):
    icd10_code: str | None = None
    label: str
    onset_date: date | None = None
    status: str = "active"


class MedicationCreate(BaseModel):
    rxnorm_code: str | None = None
    label: str
    dose: str | None = None


class AllergyCreate(BaseModel):
    substance: str
    reaction: str | None = None
    severity: str = "moderate"


class VitalCreate(BaseModel):
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    hr: int | None = None
    spo2: float | None = None
    temp_c: float | None = None
    glucose_mg_dl: int | None = None
    notes: str | None = None


class DemographicsPayload(BaseModel):
    dob: date | None = None
    sex: str | None = None
    ethnicity: str | None = None


class PatientCreateRequest(BaseModel):
    display_name: str
    external_mrn: str | None = None
    demographics: DemographicsPayload = Field(default_factory=DemographicsPayload)
    conditions: list[ConditionCreate] = Field(default_factory=list)
    medications: list[MedicationCreate] = Field(default_factory=list)
    allergies: list[AllergyCreate] = Field(default_factory=list)
    vitals: list[VitalCreate] = Field(default_factory=list)


class PatientSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    external_mrn: str | None
    created_at: datetime


class PatientListResponse(BaseModel):
    items: list[PatientSummaryResponse]
    total: int


class PatientDetailResponse(BaseModel):
    id: UUID
    display_name: str
    external_mrn: str | None
    demographics: DemographicsPayload
    conditions: list[dict[str, Any]]
    medications: list[dict[str, Any]]
    allergies: list[dict[str, Any]]
    vitals: list[dict[str, Any]]
    created_at: datetime

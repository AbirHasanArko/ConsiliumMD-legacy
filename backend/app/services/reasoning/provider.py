"""Reasoning provider protocol — the contract the rest of the system uses.

A superset of the fields CARMA's `CARMAResponse` already returns. Phase 2's
`CARMAResponseAdapter` populates this from CARMA's Pydantic models.
"""
from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from app.services.reasoning.states import ConflictTypeLabel, RoutingDecision


class PatientContext(BaseModel):
    age: int | None = None
    sex: str | None = None
    conditions: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    lab_values: dict[str, Any] = Field(default_factory=dict)
    vital_signs: dict[str, Any] = Field(default_factory=dict)


class ElicitOption(BaseModel):
    id: str
    label: str
    description: str = ""


class ReasoningStep(BaseModel):
    step: str
    detail: str = ""
    timestamp_ms: float | None = None


class EvidenceCitation(BaseModel):
    external_passage_id: str
    source_body: str
    document_title: str
    section: str
    evidence_grade: str
    study_design: str
    relevance_score: float
    quality_score: float
    excerpt: str


class ReasoningRequest(BaseModel):
    case_id: UUID
    decision_class: str
    patient_context: PatientContext
    prior_snapshot_id: UUID | None = None
    elicit_response: dict[str, Any] | None = None


class ReasoningResponse(BaseModel):
    routing: RoutingDecision
    conflict_label: ConflictTypeLabel
    recommendation_text: str
    primary_evidence_grade: str
    tradeoff_statement: str | None = None
    elicit_question: str | None = None
    elicit_options: list[ElicitOption] = Field(default_factory=list)
    escalation_reason: str | None = None
    identifiability_flag: bool | None = None
    confidence: float
    uncertainty_decomposition: dict[str, float] = Field(default_factory=dict)
    safety_verdict: str = "pass"
    safety_issues: list[str] = Field(default_factory=list)
    evidence_citations: list[EvidenceCitation] = Field(default_factory=list)
    reasoning_trail: list[ReasoningStep] = Field(default_factory=list)
    model_version_name: str
    retrieval_trace_id: str | None = None
    latency_ms: float = 0.0


class ReasoningProvider(Protocol):
    name: str

    def reason(self, request: ReasoningRequest) -> ReasoningResponse: ...

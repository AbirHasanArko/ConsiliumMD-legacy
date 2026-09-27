"""Recommendation + reasoning snapshot + action schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ElicitOption(BaseModel):
    id: str
    label: str
    description: str = ""


class ReasoningStep(BaseModel):
    step: str
    detail: str = ""
    timestamp_ms: float | None = None


class EvidenceCitationResponse(BaseModel):
    id: UUID
    external_passage_id: str
    source_body: str
    document_title: str
    section: str
    evidence_grade: str
    study_design: str
    relevance_score: float
    quality_score: float
    excerpt: str


class RecommendationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    state: str
    created_at: datetime
    decided_at: datetime | None


class RecommendationResponse(BaseModel):
    id: UUID
    case_id: UUID
    state: str
    final_recommendation_text: str | None
    final_rationale: str | None
    decided_at: datetime | None
    created_at: datetime
    latest_snapshot_id: UUID | None
    snapshot: dict[str, Any] | None = None
    citations: list[EvidenceCitationResponse] = Field(default_factory=list)


class ActionResponse(BaseModel):
    recommendation_id: UUID
    state: str
    decided_at: datetime | None
    final_recommendation_text: str | None
    final_rationale: str | None


class AcceptRequest(BaseModel):
    pass


class OverrideRequest(BaseModel):
    rationale: str = Field(min_length=1)


class EscalateRequest(BaseModel):
    note: str | None = None


class ElicitRequest(BaseModel):
    selected_option_id: str = Field(min_length=1)
    free_text_response: str | None = None


class RequestEvidenceResponse(BaseModel):
    recommendation_id: UUID
    state: str
    snapshot_sequence: int


class ResolveRequest(BaseModel):
    final_recommendation_text: str = Field(min_length=1)
    rationale: str = Field(min_length=1)

"""Audit + model-version schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: UUID | None
    action: str
    target_type: str
    target_id: UUID | None
    occurred_at: datetime
    ip: str | None
    user_agent: str | None
    payload_json: str


class AuditExportRow(BaseModel):
    occurred_at: datetime
    actor_user_id: str
    action: str
    target_type: str
    target_id: str
    ip: str
    user_agent: str
    payload_json: str


class ModelVersionUsageResponse(BaseModel):
    model_version_id: UUID
    provider: str
    name: str
    is_active: bool
    recommendation_count: int

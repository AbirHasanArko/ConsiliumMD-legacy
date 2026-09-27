"""Audit + model-version router (admin-only)."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.rbac import ROLE_ADMIN
from app.deps import db_dep, require_permission, require_role
from app.models import (
    AuditEvent,
    ModelVersion,
    Recommendation,
    ReasoningSnapshot,
    User,
)
from app.schemas.audit import (
    AuditEventResponse,
    ModelVersionUsageResponse,
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=list[AuditEventResponse])
def list_events(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_ADMIN)),
    actor_user_id: UUID | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: UUID | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[AuditEventResponse]:
    q = db.query(AuditEvent).order_by(AuditEvent.occurred_at.desc())
    if actor_user_id:
        q = q.filter(AuditEvent.actor_user_id == actor_user_id)
    if action:
        q = q.filter(AuditEvent.action == action)
    if target_type:
        q = q.filter(AuditEvent.target_type == target_type)
    if target_id:
        q = q.filter(AuditEvent.target_id == target_id)
    if from_:
        q = q.filter(AuditEvent.occurred_at >= from_)
    if to:
        q = q.filter(AuditEvent.occurred_at <= to)
    q = q.limit(limit)
    return [
        AuditEventResponse(
            id=e.id,
            actor_user_id=e.actor_user_id,
            action=e.action,
            target_type=e.target_type,
            target_id=e.target_id,
            occurred_at=e.occurred_at,
            ip=e.ip,
            user_agent=e.user_agent,
            payload_json=e.payload_json,
        )
        for e in q
    ]


@router.get("/events/export.csv")
def export_csv(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_ADMIN)),
    _export_perm: User = Depends(require_permission("audit:export")),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
) -> StreamingResponse:
    q = db.query(AuditEvent).order_by(AuditEvent.occurred_at.asc())
    if from_:
        q = q.filter(AuditEvent.occurred_at >= from_)
    if to:
        q = q.filter(AuditEvent.occurred_at <= to)
    events = q.all()

    def _iter():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "occurred_at",
                "actor_user_id",
                "action",
                "target_type",
                "target_id",
                "ip",
                "user_agent",
                "payload_json",
            ]
        )
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        for e in events:
            writer.writerow(
                [
                    e.occurred_at.isoformat(),
                    str(e.actor_user_id) if e.actor_user_id else "",
                    e.action,
                    e.target_type,
                    str(e.target_id) if e.target_id else "",
                    e.ip or "",
                    e.user_agent or "",
                    e.payload_json,
                ]
            )
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    return StreamingResponse(
        _iter(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_events.csv"},
    )


@router.get("/model-versions", response_model=list[ModelVersionUsageResponse])
def model_versions(
    db: Session = Depends(db_dep),
    _u: User = Depends(require_role(ROLE_ADMIN)),
) -> list[ModelVersionUsageResponse]:
    rows = (
        db.query(
            ModelVersion.id,
            ModelVersion.provider,
            ModelVersion.name,
            ModelVersion.is_active,
            func.count(Recommendation.id.distinct()),
        )
        .outerjoin(
            ReasoningSnapshot,
            ModelVersion.id == ReasoningSnapshot.model_version_id,
        )
        .outerjoin(
            Recommendation,
            Recommendation.id == ReasoningSnapshot.recommendation_id,
        )
        .group_by(ModelVersion.id)
        .all()
    )
    return [
        ModelVersionUsageResponse(
            model_version_id=row[0],
            provider=row[1],
            name=row[2],
            is_active=row[3],
            recommendation_count=row[4] or 0,
        )
        for row in rows
    ]

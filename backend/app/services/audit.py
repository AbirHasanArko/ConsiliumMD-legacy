"""Append-only audit event writer.

The writer exposes a single `record()` method. There is intentionally no
`update()` or `delete()` — the audit log is append-only by construction.
On Postgres, a DB trigger also enforces this; on SQLite (dev) the
service-layer contract is the only line of defense.
"""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditEvent


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        action: str,
        target_type: str,
        target_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            action=action,
            target_type=target_type,
            target_id=target_id,
            actor_user_id=actor_user_id,
            ip=ip,
            user_agent=user_agent,
            payload_json=json.dumps(payload or {}, default=str),
        )
        self.db.add(event)
        # The caller is expected to commit the surrounding transaction.
        return event


def client_ip(request) -> str | None:
    # Honor X-Forwarded-For if a reverse proxy is in front; otherwise direct.
    xff = request.headers.get("x-forwarded-for") if request else None
    if xff:
        return xff.split(",")[0].strip()
    if request and request.client:
        return request.client.host
    return None

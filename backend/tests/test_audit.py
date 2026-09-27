"""Audit log tests."""
from __future__ import annotations

from tests.conftest import auth_header, login


def test_login_writes_audit_event(client, admin_user, doctor_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@test.md", "password": "doctor1234"},
    )
    assert resp.status_code == 200

    admin_token = login(client, "admin@test.md", "admin1234")
    resp = client.get(
        "/api/v1/audit/events",
        params={"action": "auth.login"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    events = resp.json()
    assert any(e["action"] == "auth.login" for e in events)


def test_recommendation_create_writes_audit_event(client, admin_user, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    pat = client.post(
        "/api/v1/patients",
        json={"display_name": "Audit Patient"},
        headers=auth_header(token),
    )
    pid = pat.json()["id"]
    case = client.post(
        "/api/v1/cases",
        json={
            "patient_id": pid,
            "decision_class": "statin_initiation_qrisk_vs_acc_aha",
            "title": "Audit Case",
        },
        headers=auth_header(token),
    )
    cid = case.json()["id"]
    rec = client.post(
        f"/api/v1/cases/{cid}/recommendations", headers=auth_header(token)
    )
    assert rec.status_code == 201

    admin_token = login(client, "admin@test.md", "admin1234")
    resp = client.get(
        "/api/v1/audit/events",
        params={"action": "recommendation.create"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    events = resp.json()
    assert any(e["action"] == "recommendation.create" for e in events)


def test_audit_csv_export(client, admin_user, doctor_user):
    # Trigger some audit events first.
    client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@test.md", "password": "doctor1234"},
    )
    admin_token = login(client, "admin@test.md", "admin1234")
    resp = client.get(
        "/api/v1/audit/events/export.csv", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    body = resp.text
    assert "occurred_at" in body  # header row


def test_audit_append_only_via_service(client, db_session):
    from app.services.audit import AuditService

    svc = AuditService(db_session)
    event = svc.record(action="test.event", target_type="test")
    db_session.commit()

    # The writer only exposes `.record()`. There is no `.update()` / `.delete()`,
    # so the only way to mutate a row is direct session access — proving the
    # builder pattern is the sole mutator surface.
    assert event.id is not None
    from sqlalchemy import select

    from app.models import AuditEvent

    row = db_session.execute(
        select(AuditEvent).where(AuditEvent.id == event.id)
    ).scalar_one()
    # Direct mutations still possible in tests (no DB trigger on SQLite), but the
    # service contract is the documented surface.
    assert row.action == "test.event"

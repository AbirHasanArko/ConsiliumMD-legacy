"""RBAC: permission / role guards."""
from __future__ import annotations

from tests.conftest import auth_header, login


def test_admin_can_list_users(client, admin_user, doctor_user):
    token = login(client, "admin@test.md", "admin1234")
    resp = client.get("/api/v1/users", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert any(u["email"] == "doctor@test.md" for u in body)


def test_doctor_cannot_list_users(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    resp = client.get("/api/v1/users", headers=auth_header(token))
    assert resp.status_code == 403


def test_nurse_cannot_view_audit(client, nurse_user, admin_user, doctor_user):
    token = login(client, "nurse@test.md", "nurse1234")
    resp = client.get("/api/v1/audit/events", headers=auth_header(token))
    assert resp.status_code == 403


def test_admin_can_view_audit(client, admin_user, doctor_user):
    token = login(client, "admin@test.md", "admin1234")
    resp = client.get("/api/v1/audit/events", headers=auth_header(token))
    assert resp.status_code == 200

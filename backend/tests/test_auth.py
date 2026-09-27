"""Auth tests."""
from __future__ import annotations

from app.core.security import create_access_token, decode_token


def test_login_success(client, doctor_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@test.md", "password": "doctor1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_bad_password(client, doctor_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@test.md", "password": "nope"},
    )
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.md", "password": "whatever"},
    )
    assert resp.status_code == 401


def test_me_endpoint(client, doctor_user):
    from tests.conftest import auth_header, login

    token = login(client, "doctor@test.md", "doctor1234")
    resp = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "doctor@test.md"
    assert "doctor" in body["roles"]


def test_me_missing_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_jwt_roundtrip():
    from uuid import uuid4

    uid = str(uuid4())
    token = create_access_token(uid)
    payload = decode_token(token)
    assert payload["sub"] == uid
    assert payload["type"] == "access"

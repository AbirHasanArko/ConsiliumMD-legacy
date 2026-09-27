"""Patient tests."""
from __future__ import annotations

from datetime import date

from tests.conftest import auth_header, login


def _create_patient(client, doctor_token) -> str:
    resp = client.post(
        "/api/v1/patients",
        json={
            "display_name": "Test Patient",
            "demographics": {"sex": "female"},
            "conditions": [{"label": "hypertension"}],
            "medications": [{"label": "lisinopril", "dose": "10 mg"}],
            "allergies": [{"substance": "penicillin", "severity": "moderate"}],
            "vitals": [{"systolic_bp": 130, "diastolic_bp": 82, "hr": 70}],
        },
        headers=auth_header(doctor_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_create_patient_and_get(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    pid = _create_patient(client, token)
    resp = client.get(f"/api/v1/patients/{pid}", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["display_name"] == "Test Patient"
    assert any(a["substance"] == "penicillin" for a in body["allergies"])


def test_add_vitals_to_patient(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    pid = _create_patient(client, token)
    resp = client.post(
        f"/api/v1/patients/{pid}/vitals",
        json={"systolic_bp": 128, "diastolic_bp": 80, "hr": 75},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["vitals"]) >= 2


def test_create_patient_requires_case_create_permission(client, nurse_user):
    token = login(client, "nurse@test.md", "nurse1234")
    resp = client.post(
        "/api/v1/patients",
        json={"display_name": "Should fail"},
        headers=auth_header(token),
    )
    assert resp.status_code == 403

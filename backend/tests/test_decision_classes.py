"""Decision class scope enforcement."""
from __future__ import annotations

from tests.conftest import auth_header, login


def test_list_decision_classes_includes_held_back(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    resp = client.get("/api/v1/decision-classes", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    by_class = {c["decision_class"]: c for c in body}
    assert by_class["bp_target_jnc8_vs_acc_aha_2017"]["in_scope"] is True
    assert by_class["opioid_threshold"]["in_scope"] is False
    assert by_class["eol_care_intensity"]["requires_ethics_review"] is True


def test_create_case_with_out_of_scope_class_is_409(client, doctor_user):
    from datetime import date

    token = login(client, "doctor@test.md", "doctor1234")
    # Create a patient first.
    pat = client.post(
        "/api/v1/patients",
        json={"display_name": "Will fail case"},
        headers=auth_header(token),
    )
    assert pat.status_code == 201, pat.text
    pid = pat.json()["id"]

    resp = client.post(
        "/api/v1/cases",
        json={
            "patient_id": pid,
            "decision_class": "opioid_threshold",
            "title": "should be blocked",
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 409
    assert "decision_class_not_in_mvp_scope" in resp.json()["detail"]


def test_create_case_with_unknown_class_is_409(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    pat = client.post(
        "/api/v1/patients",
        json={"display_name": "Will fail unknown class"},
        headers=auth_header(token),
    )
    pid = pat.json()["id"]
    resp = client.post(
        "/api/v1/cases",
        json={
            "patient_id": pid,
            "decision_class": "hypothetical_class",
            "title": "should fail",
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 409

"""Recommendation lifecycle tests covering all four RoutingDecision states."""
from __future__ import annotations

from tests.conftest import auth_header, login


def _bootstrap_case(client, token: str, decision_class: str = "statin_initiation_qrisk_vs_acc_aha") -> str:
    pat = client.post(
        "/api/v1/patients",
        json={"display_name": f"Patient {decision_class}"},
        headers=auth_header(token),
    )
    pid = pat.json()["id"]
    resp = client.post(
        "/api/v1/cases",
        json={"patient_id": pid, "decision_class": decision_class, "title": "test"},
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_full_answer_flow(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    case_id = _bootstrap_case(client, token)
    resp = client.post(
        f"/api/v1/cases/{case_id}/recommendations", headers=auth_header(token)
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    # Default seeded case is statin — expected_routing "answer" -> "answered".
    assert body["state"] in ("answered", "retrieved")
    assert body["snapshot"] is not None
    assert body["snapshot"]["routing_decision"] in ("answer", "retrieve", "elicit", "escalate")

    # If in answered state, accept; else check the state is reasonable.
    if body["state"] == "answered":
        accept = client.post(
            f"/api/v1/recommendations/{body['id']}/accept",
            headers=auth_header(token),
        )
        assert accept.status_code == 200
        assert accept.json()["state"] == "accepted"


def test_retrieve_flow_yields_answer_state(client, doctor_user, reviewer_user):
    token = login(client, "doctor@test.md", "doctor1234")
    # anticoagulation is "retrieve_then_answer" in seeded cases.
    case_id = _bootstrap_case(client, token, "anticoagulation_af_chadsvasc")
    resp = client.post(
        f"/api/v1/cases/{case_id}/recommendations", headers=auth_header(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["state"] == "retrieved"
    assert body["snapshot"]["routing_decision"] == "retrieve"

    # Requesting more evidence advances to answered.
    req = client.post(
        f"/api/v1/recommendations/{body['id']}/request-evidence",
        headers=auth_header(token),
    )
    assert req.status_code == 200
    assert req.json()["state"] == "answered"


def test_elicit_flow_with_preference_submission(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    case_id = _bootstrap_case(client, token, "bp_target_jnc8_vs_acc_aha_2017")
    resp = client.post(
        f"/api/v1/cases/{case_id}/recommendations", headers=auth_header(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["state"] == "elicit_pending"
    assert body["snapshot"]["conflict_label"] == "judgment_call"
    options = body["snapshot"]["elicit_options"]
    assert options, "judgment-call case must include elicit options"

    submit = client.post(
        f"/api/v1/recommendations/{body['id']}/elicit",
        json={"selected_option_id": options[0]["id"]},
        headers=auth_header(token),
    )
    assert submit.status_code == 200
    assert submit.json()["state"] == "answered"


def test_escalate_then_reviewer_resolves(client, doctor_user, reviewer_user):
    token = login(client, "doctor@test.md", "doctor1234")
    case_id = _bootstrap_case(client, token, "psa_screening_uspstf_vs_aua")
    resp = client.post(
        f"/api/v1/cases/{case_id}/recommendations", headers=auth_header(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    # psa_screening is "escalate" -> rec lands in 'escalated' state
    # directly. The reviewer's queue should already contain it.
    assert body["state"] == "escalated"
    assert body["snapshot"]["conflict_label"] == "under_review"

    reviewer_token = login(client, "reviewer@test.md", "reviewer1234")
    queue = client.get("/api/v1/review/queue", headers=auth_header(reviewer_token))
    assert queue.status_code == 200
    queue_ids = [r["id"] for r in queue.json()]
    assert body["id"] in queue_ids

    resolve = client.post(
        f"/api/v1/review/{body['id']}/resolve",
        json={
            "final_recommendation_text": "Shared decision; document preference.",
            "rationale": "Non-identifiable; patient values discussed.",
        },
        headers=auth_header(reviewer_token),
    )
    assert resolve.status_code == 200
    assert resolve.json()["state"] == "resolved"


def test_override_requires_rationale(client, doctor_user):
    token = login(client, "doctor@test.md", "doctor1234")
    case_id = _bootstrap_case(client, token)
    rec = client.post(
        f"/api/v1/cases/{case_id}/recommendations", headers=auth_header(token)
    ).json()
    if rec["state"] != "answered":
        # Force an answered state so we can test override.
        req = client.post(
            f"/api/v1/recommendations/{rec['id']}/request-evidence",
            headers=auth_header(token),
        )
        rec = client.get(
            f"/api/v1/recommendations/{rec['id']}",
            headers=auth_header(token),
        ).json()

    bad = client.post(
        f"/api/v1/recommendations/{rec['id']}/override",
        json={"rationale": ""},
        headers=auth_header(token),
    )
    assert bad.status_code in (400, 422)


def test_invalid_state_transition_is_409(client, doctor_user, reviewer_user):
    token = login(client, "doctor@test.md", "doctor1234")
    case_id = _bootstrap_case(client, token)
    rec = client.post(
        f"/api/v1/cases/{case_id}/recommendations", headers=auth_header(token)
    ).json()
    # Trying to resolve a non-escalated recommendation as a reviewer should 409.
    reviewer_token = login(
        client, "reviewer@test.md", "reviewer1234"
    )
    bad = client.post(
        f"/api/v1/review/{rec['id']}/resolve",
        json={"final_recommendation_text": "X", "rationale": "Y"},
        headers=auth_header(reviewer_token),
    )
    # 409 if state is not in {escalated, under_review}; 403 if reviewer can't even see it.
    assert bad.status_code in (403, 409)

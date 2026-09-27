"""Safety auditor tests."""
from __future__ import annotations

from app.services.safety_auditor import audit_recommendation


def test_allergy_match_is_fail():
    report = audit_recommendation(
        recommendation_text="Recommend starting aspirin 81 mg daily.",
        allergies=["aspirin"],
    )
    assert report.verdict == "fail"
    assert any("aspirin" in issue for issue in report.issues)


def test_duplicate_med_is_caution():
    report = audit_recommendation(
        recommendation_text="Continue metformin 500 mg BID.",
        active_medications=["metformin"],
    )
    assert report.verdict == "caution"
    assert any("metformin" in issue for issue in report.issues)


def test_no_issues_pass():
    report = audit_recommendation(
        recommendation_text="Order lipid panel in 12 weeks.",
    )
    assert report.verdict == "pass"
    assert report.issues == []

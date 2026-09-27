"""Patient-record safety auditor.

Pure rule check against the patient's own record (allergies, medications,
current conditions). Runs server-side before a recommendation is shown.

This is intentionally simple in Phase 1 — a regex/keyword match against the
recommendation text for substances the patient is allergic to, plus a
duplicate-medication check. Phase 3 can swap in a richer rule engine.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class SafetyReport:
    verdict: str = "pass"  # "pass" | "caution" | "fail"
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "issues": self.issues}


def audit_recommendation(
    *,
    recommendation_text: str,
    allergies: Iterable[str] = (),
    active_medications: Iterable[str] = (),
) -> SafetyReport:
    report = SafetyReport()
    text = (recommendation_text or "").lower()

    # Allergy check
    for substance in allergies:
        if not substance:
            continue
        pattern = r"\b" + re.escape(substance.lower()) + r"\b"
        if re.search(pattern, text):
            report.issues.append(
                f"allergy_match:{substance}"
            )
            report.verdict = "fail"
            return report

    # Duplicate medication check
    meds = [m.lower() for m in active_medications if m]
    for med in meds:
        pattern = r"\b" + re.escape(med) + r"\b"
        if re.search(pattern, text):
            report.verdict = "caution" if report.verdict == "pass" else report.verdict
            report.issues.append(f"already_on:{med}")

    return report

"""Decision-class scope enforcement.

The MVP deliberately excludes two normative classes from the research benchmark:
- `opioid_threshold` — addiction risk needs ethics review
- `eol_care_intensity` — coercion risk at end of life needs ethics review

This service is the gate. Both `clinical_cases.decision_class` and
`recommendations` (transitively, via their case) must pass through here.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import DecisionClassScope

OUT_OF_SCOPE_CLASSES = {"opioid_threshold", "eol_care_intensity"}


def assert_decision_class_in_scope(db: Session, decision_class: str) -> None:
    """Raise 409 if the class is registered as out-of-scope."""
    row = db.get(DecisionClassScope, decision_class)
    if row is None:
        # Unknown decision classes are rejected too — the spec says the
        # product must not claim coverage the paper hasn't validated.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"decision_class_not_in_mvp_scope:{decision_class}",
        )
    if not row.in_scope:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"decision_class_not_in_mvp_scope:{decision_class}",
        )


def is_in_scope(db: Session, decision_class: str) -> bool:
    row = db.get(DecisionClassScope, decision_class)
    return row is not None and row.in_scope

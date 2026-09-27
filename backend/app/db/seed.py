"""Seed demo data.

Idempotent: re-runs are safe. Skipped if `SEED_DEMO_DATA=false` in env.
"""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from app.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    ClinicalCase,
    DecisionClassScope,
    Patient,
    PatientAllergy,
    PatientCondition,
    PatientDemographics,
    PatientMedication,
    PatientVital,
    Role,
    User,
    UserRole,
)
from app.services.reasoning.mock_provider import load_seeded_decision_classes


_DEMO_USERS = [
    {
        "email": "admin@consilium.md",
        "full_name": "Avery Patel",
        "password": "admin1234",
        "roles": ["admin"],
    },
    {
        "email": "doctor@consilium.md",
        "full_name": "Dr. Lin Hayashi",
        "password": "doctor1234",
        "roles": ["doctor"],
    },
    {
        "email": "reviewer@consilium.md",
        "full_name": "Dr. Morgan Reyes",
        "password": "reviewer1234",
        "roles": ["senior_clinician"],
    },
    {
        "email": "nurse@consilium.md",
        "full_name": "Nurse Casey Quinn",
        "password": "nurse1234",
        "roles": ["nurse"],
    },
]


def _ensure_roles(db) -> dict[str, Role]:
    existing = {r.name: r for r in db.query(Role).all()}
    defaults = {
        "admin": "Full administrative access",
        "doctor": "Treating clinician",
        "senior_clinician": "Senior reviewer for escalations",
        "nurse": "Clinical staff — read/execute only",
    }
    out: dict[str, Role] = {}
    for name, desc in defaults.items():
        if name in existing:
            out[name] = existing[name]
            continue
        r = Role(name=name, description=desc)
        db.add(r)
        out[name] = r
    db.flush()
    return out


def _ensure_demo_users(db, roles: dict[str, Role]) -> dict[str, User]:
    out: dict[str, User] = {}
    for spec in _DEMO_USERS:
        user = db.query(User).filter_by(email=spec["email"]).first()
        if user is None:
            user = User(
                email=spec["email"],
                full_name=spec["full_name"],
                password_hash=hash_password(spec["password"]),
                is_active=True,
            )
            db.add(user)
            db.flush()
        for role_name in spec["roles"]:
            role = roles[role_name]
            existing_link = (
                db.query(UserRole)
                .filter_by(user_id=user.id, role_id=role.id)
                .first()
            )
            if existing_link is None:
                db.add(UserRole(user_id=user.id, role_id=role.id))
        out[spec["email"]] = user
    db.flush()
    return out


def _ensure_decision_class_scopes(db) -> None:
    for entry in load_seeded_decision_classes():
        existing = db.get(DecisionClassScope, entry["decision_class"])
        if existing is None:
            db.add(
                DecisionClassScope(
                    decision_class=entry["decision_class"],
                    in_scope=entry.get("in_scope", True),
                    requires_ethics_review=entry.get(
                        "requires_ethics_review", False
                    ),
                    display_label=entry["display_label"],
                    notes=entry.get("notes", ""),
                )
            )


def _ensure_demo_patients_and_cases(db, users: dict[str, User]) -> None:
    """Create the 6 demo patients + cases used in the README demo script."""
    doctor = users["doctor@consilium.md"]
    reviewer = users["reviewer@consilium.md"]

    seeded = [
        {
            "display_name": "Margaret Chen",
            "decision_class": "statin_initiation_qrisk_vs_acc_aha",
            "title": "Primary prevention statin for 62yo with LDL 145",
            "sex": "female",
            "age": 62,
            "conditions": [
                ("I10", "hypertension"),
                ("E11", "type_2_diabetes"),
            ],
            "medications": [("metformin", "500 mg BID"), ("lisinopril", "10 mg daily")],
            "vitals": {"systolic_bp": 138, "diastolic_bp": 82, "hr": 72},
        },
        {
            "display_name": "James O'Brien",
            "decision_class": "anticoagulation_af_chadsvasc",
            "title": "CHA2DS2-VASc=2 anticoagulation choice",
            "sex": "male",
            "age": 71,
            "conditions": [
                ("I48", "atrial_fibrillation_paroxysmal"),
                ("N18", "ckd_stage_3a"),
            ],
            "medications": [("amlodipine", "5 mg daily")],
            "vitals": {"systolic_bp": 142, "diastolic_bp": 86, "hr": 88},
        },
        {
            "display_name": "Priya Raman",
            "decision_class": "bp_target_jnc8_vs_acc_aha_2017",
            "title": "BP target for 58yo with controlled HTN and DM",
            "sex": "female",
            "age": 58,
            "conditions": [("I10", "hypertension"), ("E11", "type_2_diabetes")],
            "medications": [("lisinopril", "10 mg daily"), ("metformin", "500 mg BID")],
            "vitals": {"systolic_bp": 134, "diastolic_bp": 80, "hr": 70},
        },
        {
            "display_name": "Ahmed Al-Sayed",
            "decision_class": "psa_screening_uspstf_vs_aua",
            "title": "PSA screening in 67yo with family history",
            "sex": "male",
            "age": 67,
            "conditions": [("Z80", "family_history_prostate_cancer")],
            "medications": [],
            "vitals": {},
        },
        {
            "display_name": "Sofia Martinez",
            "decision_class": "hba1c_target",
            "title": "HbA1c target for 49yo with T2DM and CKD",
            "sex": "female",
            "age": 49,
            "conditions": [("E11", "type_2_diabetes"), ("N18", "ckd_stage_3a")],
            "medications": [("metformin", "1000 mg BID")],
            "vitals": {"systolic_bp": 128, "diastolic_bp": 78, "hr": 76},
        },
        {
            "display_name": "Daniel Park",
            "decision_class": "egfr_drug_cutoff",
            "title": "SGLT2 initiation in 71yo with eGFR 28",
            "sex": "male",
            "age": 71,
            "conditions": [("E11", "type_2_diabetes"), ("N18", "ckd_stage_3b")],
            "medications": [("metformin", "1000 mg BID"), ("lisinopril", "10 mg daily")],
            "vitals": {"systolic_bp": 132, "diastolic_bp": 79, "hr": 80},
        },
    ]

    for spec in seeded:
        existing = (
            db.query(Patient).filter_by(display_name=spec["display_name"]).first()
        )
        if existing is None:
            patient = Patient(display_name=spec["display_name"])
            db.add(patient)
            db.flush()
            db.add(
                PatientDemographics(
                    patient_id=patient.id,
                    dob=date(2024 - spec["age"], 1, 1),
                    sex=spec["sex"],
                )
            )
            for icd, label in spec["conditions"]:
                db.add(
                    PatientCondition(
                        patient_id=patient.id,
                        icd10_code=icd,
                        label=label,
                    )
                )
            for label, dose in spec["medications"]:
                db.add(
                    PatientMedication(
                        patient_id=patient.id,
                        label=label,
                        dose=dose,
                    )
                )
            if spec["vitals"]:
                db.add(
                    PatientVital(
                        patient_id=patient.id,
                        systolic_bp=spec["vitals"].get("systolic_bp"),
                        diastolic_bp=spec["vitals"].get("diastolic_bp"),
                        hr=spec["vitals"].get("hr"),
                    )
                )
        else:
            patient = existing

        # Case row, if missing.
        case = (
            db.query(ClinicalCase)
            .filter_by(patient_id=patient.id, decision_class=spec["decision_class"])
            .first()
        )
        if case is None:
            case = ClinicalCase(
                patient_id=patient.id,
                doctor_id=doctor.id,
                decision_class=spec["decision_class"],
                title=spec["title"],
            )
            db.add(case)


def main() -> None:
    settings = get_settings()
    if not settings.seed_demo_data:
        print("SEED_DEMO_DATA=false — skipping seed.")
        return

    db = SessionLocal()
    try:
        roles = _ensure_roles(db)
        users = _ensure_demo_users(db, roles)
        _ensure_decision_class_scopes(db)
        _ensure_demo_patients_and_cases(db, users)
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

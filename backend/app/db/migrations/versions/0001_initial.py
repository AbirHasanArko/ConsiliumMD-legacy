"""initial schema (SQLite-friendly)

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-15 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    # 36-char text primary key; portable across SQLite and Postgres.
    return sa.String(length=36)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", _uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", _uuid(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
    )

    op.create_table(
        "patients",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("external_mrn", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "patient_demographics",
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(length=16), nullable=True),
        sa.Column("ethnicity", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "patient_conditions",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("icd10_code", sa.String(length=16), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("onset_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.create_index("ix_patient_conditions_patient_id", "patient_conditions", ["patient_id"])

    op.create_table(
        "patient_medications",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rxnorm_code", sa.String(length=32), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("dose", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_patient_medications_patient_id", "patient_medications", ["patient_id"])

    op.create_table(
        "patient_allergies",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("substance", sa.String(length=255), nullable=False),
        sa.Column("reaction", sa.String(length=255), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="moderate"),
    )
    op.create_index("ix_patient_allergies_patient_id", "patient_allergies", ["patient_id"])

    op.create_table(
        "patient_vitals",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("systolic_bp", sa.Integer(), nullable=True),
        sa.Column("diastolic_bp", sa.Integer(), nullable=True),
        sa.Column("hr", sa.Integer(), nullable=True),
        sa.Column("spo2", sa.Float(), nullable=True),
        sa.Column("temp_c", sa.Float(), nullable=True),
        sa.Column("glucose_mg_dl", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_patient_vitals_patient_id", "patient_vitals", ["patient_id"])

    op.create_table(
        "decision_class_scopes",
        sa.Column("decision_class", sa.String(length=128), primary_key=True),
        sa.Column("in_scope", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requires_ethics_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("display_label", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "clinical_cases",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", _uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("senior_reviewer_id", _uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision_class", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_clinical_cases_patient_id", "clinical_cases", ["patient_id"])
    op.create_index("ix_clinical_cases_doctor_id", "clinical_cases", ["doctor_id"])
    op.create_index("ix_clinical_cases_decision_class", "clinical_cases", ["decision_class"])

    op.create_table(
        "model_versions",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_model_versions_provider", "model_versions", ["provider"])

    op.create_table(
        "recommendations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("case_id", _uuid(), sa.ForeignKey("clinical_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("final_recommendation_text", sa.Text(), nullable=True),
        sa.Column("final_rationale", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recommendations_case_id", "recommendations", ["case_id"])
    op.create_index("ix_recommendations_state", "recommendations", ["state"])

    op.create_table(
        "reasoning_snapshots",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("recommendation_id", _uuid(), sa.ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version_id", _uuid(), sa.ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("routing_decision", sa.String(length=16), nullable=False),
        sa.Column("conflict_label", sa.String(length=32), nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("tradeoff_statement", sa.Text(), nullable=True),
        sa.Column("elicit_question", sa.Text(), nullable=True),
        sa.Column("elicit_options_json", sa.Text(), nullable=True),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("identifiability_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("uncertainty_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("safety_verdict", sa.String(length=16), nullable=False, server_default="pass"),
        sa.Column("safety_issues_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("reasoning_trail_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_evidence_grade", sa.String(length=16), nullable=False, server_default="moderate"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reasoning_snapshots_recommendation_id", "reasoning_snapshots", ["recommendation_id"])
    op.create_index("ix_reasoning_snapshots_routing_decision", "reasoning_snapshots", ["routing_decision"])

    # Note: the recommendations.latest_snapshot_id FK is *not* added here
    # to keep this migration portable to SQLite (which has no support
    # for ALTER of constraints). The application enforces referential
    # integrity through the recommendation_lifecycle service; Postgres
    # deployments can add the FK with a follow-up migration using
    # op.batch_alter_table + op.create_foreign_key. We still add the
    # column itself (nullable, no FK constraint).
    op.add_column(
        "recommendations",
        sa.Column("latest_snapshot_id", _uuid(), nullable=True),
    )

    op.create_table(
        "evidence_citations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("snapshot_id", _uuid(), sa.ForeignKey("reasoning_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_passage_id", sa.String(length=64), nullable=False),
        sa.Column("source_body", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("document_title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("section", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("evidence_grade", sa.String(length=16), nullable=False, server_default="moderate"),
        sa.Column("study_design", sa.String(length=32), nullable=False, server_default="guideline"),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_evidence_citations_snapshot_id", "evidence_citations", ["snapshot_id"])

    op.create_table(
        "action_logs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("recommendation_id", _uuid(), sa.ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", _uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_action_logs_recommendation_id", "action_logs", ["recommendation_id"])
    op.create_index("ix_action_logs_action", "action_logs", ["action"])

    op.create_table(
        "elicitations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("recommendation_id", _uuid(), sa.ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("responder_user_id", _uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("presented_options_json", sa.Text(), nullable=False),
        sa.Column("selected_option_id", sa.String(length=64), nullable=False),
        sa.Column("free_text_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_elicitations_recommendation_id", "elicitations", ["recommendation_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("actor_user_id", _uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", _uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_target_type", "audit_events", ["target_type"])
    op.create_index("ix_audit_events_target_id", "audit_events", ["target_id"])
    op.create_index("ix_audit_events_occurred_at", "audit_events", ["occurred_at"])

    op.create_table(
        "consents",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("patient_id", _uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", _uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("consent_type", sa.String(length=64), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_consents_patient_id", "consents", ["patient_id"])


def downgrade() -> None:
    for table in [
        "consents",
        "audit_events",
        "elicitations",
        "action_logs",
        "evidence_citations",
        "recommendations",
        "reasoning_snapshots",
        "model_versions",
        "clinical_cases",
        "decision_class_scopes",
        "patient_vitals",
        "patient_allergies",
        "patient_medications",
        "patient_conditions",
        "patient_demographics",
        "patients",
        "user_roles",
        "roles",
        "users",
    ]:
        op.drop_table(table)

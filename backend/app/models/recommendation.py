"""Recommendation + snapshot + citation + action + elicitation models."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinical_cases.id", ondelete="CASCADE"), index=True
    )
    latest_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reasoning_snapshots.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    state: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    final_recommendation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    case = relationship("ClinicalCase", back_populates="recommendations", lazy="joined")
    # `snapshots` is queried explicitly in the API layer (recommendation
    # detail) rather than via a relationship, to avoid the
    # latest_snapshot_id <-> recommendation_id FK cycle.


class ReasoningSnapshot(Base, TimestampMixin):
    __tablename__ = "reasoning_snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), index=True
    )
    model_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT")
    )
    routing_decision: Mapped[str] = mapped_column(String(16), index=True)
    conflict_label: Mapped[str] = mapped_column(String(32))
    recommendation_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    tradeoff_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    elicit_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    elicit_options_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    identifiability_flag: Mapped[bool] = mapped_column(default=False)
    uncertainty_json: Mapped[str] = mapped_column(Text, default="{}")
    safety_verdict: Mapped[str] = mapped_column(String(16), default="pass")
    safety_issues_json: Mapped[str] = mapped_column(Text, default="[]")
    reasoning_trail_json: Mapped[str] = mapped_column(Text, default="[]")
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    sequence_number: Mapped[int] = mapped_column(Integer, default=0)
    primary_evidence_grade: Mapped[str] = mapped_column(String(16), default="moderate")

    model_version = relationship("ModelVersion", lazy="joined")
    evidence_citations: Mapped[list["EvidenceCitation"]] = relationship(
        "EvidenceCitation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EvidenceCitation(Base):
    __tablename__ = "evidence_citations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("reasoning_snapshots.id", ondelete="CASCADE"), index=True
    )
    external_passage_id: Mapped[str] = mapped_column(String(64))
    source_body: Mapped[str] = mapped_column(String(128), default="")
    document_title: Mapped[str] = mapped_column(String(255), default="")
    section: Mapped[str] = mapped_column(String(255), default="")
    evidence_grade: Mapped[str] = mapped_column(String(16), default="moderate")
    study_design: Mapped[str] = mapped_column(String(32), default="guideline")
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    excerpt: Mapped[str] = mapped_column(Text, default="")


class ActionLog(Base, TimestampMixin):
    __tablename__ = "action_logs"
    __table_args__ = (UniqueConstraint("id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), index=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), index=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")


class Elicitation(Base, TimestampMixin):
    __tablename__ = "elicitations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recommendation_id: Mapped[UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), index=True
    )
    responder_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    presented_options_json: Mapped[str] = mapped_column(Text)
    selected_option_id: Mapped[str] = mapped_column(String(64))
    free_text_response: Mapped[str | None] = mapped_column(Text, nullable=True)

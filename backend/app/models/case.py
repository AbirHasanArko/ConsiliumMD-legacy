"""ClinicalCase and DecisionClassScope models."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DecisionClassScope(Base, TimestampMixin):
    __tablename__ = "decision_class_scopes"

    decision_class: Mapped[str] = mapped_column(String(128), primary_key=True)
    in_scope: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_ethics_review: Mapped[bool] = mapped_column(Boolean, default=False)
    display_label: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text, default="")


class ClinicalCase(Base, TimestampMixin):
    __tablename__ = "clinical_cases"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    doctor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    senior_reviewer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision_class: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="open")
    patient: Mapped["Patient"] = relationship(  # noqa: F821
        "Patient", lazy="joined"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Note: a `DecisionClassScope` row is referenced via
    # `clinical_cases.decision_class` (string match on the PK), not via FK.
    # SQLAlchemy can't auto-detect that join, so we look up the scope via a
    # plain query in the API layer rather than via an ORM relationship.

    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

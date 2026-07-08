from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class DiseaseORM(Base):
    __tablename__ = "diseases"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    diagnosis_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    onset_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    resolved_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        Index("ix_diseases_patient_diagnosis_onset", "patient_profile_id", "diagnosis_name", "onset_date"),
        CheckConstraint(
            "resolved_date IS NULL OR resolved_date >= onset_date",
            name="ck_diseases_resolved_after_onset",
        ),
    )

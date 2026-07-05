from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class MedicationORM(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    drug_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)

    dose_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    dose_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dosage_text: Mapped[str | None] = mapped_column(String(500), nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        Index("ix_medications_patient_drug_start", "patient_profile_id", "drug_name", "start_date"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_medications_end_after_start",
        ),
    )
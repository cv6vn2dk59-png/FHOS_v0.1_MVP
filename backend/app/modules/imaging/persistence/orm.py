import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class ImagingStudyTypeORM(str, enum.Enum):
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    MAMMOGRAPHY = "mammography"
    OTHER = "other"


class ImagingStudyORM(Base):
    __tablename__ = "imaging_studies"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    study_type: Mapped[ImagingStudyTypeORM] = mapped_column(
        SAEnum(
            ImagingStudyTypeORM,
            name="imaging_study_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    body_part: Mapped[str] = mapped_column(String(255), nullable=False)
    study_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    facility_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    radiologist_conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        Index("ix_imaging_studies_patient_type_date", "patient_profile_id", "study_type", "study_date"),
    )
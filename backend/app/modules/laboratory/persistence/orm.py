import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum as SAEnum, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class LaboratoryInterpretationORM(str, enum.Enum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    UNKNOWN = "unknown"


class ReferenceRangeStatusORM(str, enum.Enum):
    MANUAL = "manual"
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"


class LaboratoryResultORM(Base):
    __tablename__ = "laboratory_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    reference_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    critical_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_high: Mapped[float | None] = mapped_column(Float, nullable=True)

    result_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    laboratory_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    interpretation: Mapped[LaboratoryInterpretationORM] = mapped_column(
        SAEnum(
            LaboratoryInterpretationORM,
            name="laboratory_interpretation",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=LaboratoryInterpretationORM.UNKNOWN,
        nullable=False,
        index=True,
    )

    reference_range_status: Mapped[ReferenceRangeStatusORM | None] = mapped_column(
        SAEnum(
            ReferenceRangeStatusORM,
            name="reference_range_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_laboratory_results_patient_test_date",
            "patient_profile_id",
            "test_code",
            "result_date",
        ),
    )
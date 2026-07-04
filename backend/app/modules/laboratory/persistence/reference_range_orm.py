from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class ReferenceRangeORM(Base):
    __tablename__ = "reference_ranges"

    id: Mapped[int] = mapped_column(primary_key=True)

    test_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)

    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reference_min: Mapped[float] = mapped_column(Float, nullable=False)
    reference_max: Mapped[float] = mapped_column(Float, nullable=False)

    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    laboratory_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    method: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
        Index("ix_reference_ranges_test_code_unit", "test_code", "unit"),
        CheckConstraint(
            "reference_min <= reference_max",
            name="ck_reference_ranges_min_max",
        ),
    )
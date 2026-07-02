from datetime import date, datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class PatientProfileORM(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)

    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.drug_interactions.domain.entities import MAX_PATIENT_NOTE_LENGTH
from app.persistence.base import Base


class InteractionSeverityORM(str, enum.Enum):
    CONTRAINDICATED = "contraindicated"


class DrugInteractionORM(Base):
    __tablename__ = "drug_interactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    side_a: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    side_b: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    severity: Mapped[InteractionSeverityORM] = mapped_column(
        Enum(InteractionSeverityORM, name="interaction_severity"), nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )


class PatientInteractionNoteORM(Base):
    """Interaction Evidence View, блок patient_note (S05E01/E02):
    особиста нотатка пацієнта про взаємодію двох речовин. НЕ перевірена
    системою -- unverified завжди True, ніколи не змішується з
    verified_interactions чи prescription_history.
    """

    __tablename__ = "patient_interaction_notes"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("patient_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    substance_a: Mapped[str] = mapped_column(String(255), nullable=False)
    substance_b: Mapped[str] = mapped_column(String(255), nullable=False)
    # Довжина колонки навмисно прив'язана до domain-константи, не
    # захардкожена окремим числом -- інакше зміна MAX_PATIENT_NOTE_LENGTH
    # у domain мовчки розійдеться з реальним обмеженням у БД (Alembic
    # snapshot при цьому все одно фіксує число, це нормально -- джерело
    # істини для НОВИХ міграцій лишається тут).
    note_text: Mapped[str] = mapped_column(String(MAX_PATIENT_NOTE_LENGTH), nullable=False)
    unverified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_patient_interaction_notes_patient_pair",
            "patient_profile_id", "substance_a", "substance_b",
        ),
    )

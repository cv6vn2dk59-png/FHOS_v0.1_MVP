import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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

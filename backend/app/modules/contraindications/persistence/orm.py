from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class ContraindicationORM(Base):
    """Contraindications v1 (ADR-0014, docs/SPRINT_7_E01_SUMMARY.md).

    Знання-факт з MeDIC v1: речовина (CHEBI) протипоказана при хворобі
    (MONDO). Асиметрична модель -- на відміну від DrugInteractionORM,
    тут немає pair_key() (substance і disease ніколи не міняються
    місцями) і немає severity (MeDIC v1 не надає цих даних).

    Без DB-рівня UNIQUE на (substance_chebi_id, disease_mondo_id) --
    той самий підхід, що DrugInteractionORM: дедуплікація при seed-і
    робиться на рівні скрипта (порівняння пар, що вже є в БД), не через
    constraint. Композитний індекс -- для швидкого matches()-пошуку.
    """

    __tablename__ = "contraindications"

    id: Mapped[int] = mapped_column(primary_key=True)

    substance_chebi_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    disease_mondo_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_source_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_contraindications_substance_disease",
            "substance_chebi_id", "disease_mondo_id",
        ),
    )

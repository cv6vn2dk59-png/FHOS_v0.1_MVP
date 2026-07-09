import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.base import Base


class TranslationStatusORM(str, enum.Enum):
    VERIFIED = "verified"
    AUTO_IMPORTED = "auto_imported"
    NEEDS_REVIEW = "needs_review"
    MISSING = "missing"


class NodeKindORM(str, enum.Enum):
    CHAPTER = "chapter"
    BLOCK = "block"
    CATEGORY = "category"


class SpecialCodeORM(str, enum.Enum):
    NONE = "none"
    Y = "y"
    Z = "z"


class ICD11NodeORM(Base):
    """ICD-11 v1 (ADR-0015, docs/SPRINT_7_E02_SUMMARY.md).

    id -- WHO Linearization URI або blockId, НЕ autoincrement. На
    відміну від решти ORM-моделей проекту (int PK, призначається БД),
    тут PK -- зовнішній стабільний ідентифікатор ВООЗ. parent_id --
    self-referencing FK на цю ж таблицю (дерево Chapter -> Block ->
    Category).
    """

    __tablename__ = "icd11_nodes"

    id: Mapped[str] = mapped_column(String(500), primary_key=True)

    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("icd11_nodes.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    english_title: Mapped[str] = mapped_column(Text, nullable=False)
    ukrainian_title: Mapped[str | None] = mapped_column(Text, nullable=True)

    translation_status: Mapped[TranslationStatusORM] = mapped_column(
        Enum(TranslationStatusORM, name="icd11_translation_status"), nullable=False,
    )
    node_kind: Mapped[NodeKindORM] = mapped_column(
        Enum(NodeKindORM, name="icd11_node_kind"), nullable=False, index=True,
    )
    special_code: Mapped[SpecialCodeORM] = mapped_column(
        Enum(SpecialCodeORM, name="icd11_special_code"), nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    source_release: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

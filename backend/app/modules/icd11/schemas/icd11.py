from pydantic import BaseModel, ConfigDict

from app.modules.icd11.domain.entities import NodeKind, SpecialCode, TranslationStatus


class ICD11NodeRead(BaseModel):
    """Read-only knowledge asset -- немає ICD11NodeCreate: вузли
    заповнюються через importer/seed зі статичного WHO-джерела, не
    через API (той самий підхід, що DrugInteraction -- POST існує
    лише для patient_note, не для самого knowledge asset).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: str | None
    icd_code: str | None
    english_title: str
    ukrainian_title: str | None
    translation_status: TranslationStatus
    node_kind: NodeKind
    special_code: SpecialCode
    sort_order: int
    source_release: str

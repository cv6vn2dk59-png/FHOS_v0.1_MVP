from datetime import date

from pydantic import BaseModel

from app.modules.drug_interactions.domain.entities import InteractionSeverity


class DrugInteractionRead(BaseModel):
    side_a: list[str]
    side_b: list[str]
    severity: InteractionSeverity
    description: str
    knowledge_source_id: str


class PrescriptionHistoryEntryRead(BaseModel):
    medication_a_name: str
    medication_b_name: str
    substance_a: str
    substance_b: str
    medication_a_start_date: date
    medication_a_end_date: date | None
    medication_b_start_date: date
    medication_b_end_date: date | None
    overlap_start: date
    overlap_end: date
    warning: str


class DrugInteractionCheckRead(BaseModel):
    patient_profile_id: int | None
    interactions: list[DrugInteractionRead]
    has_interactions: bool


class InteractionEvidenceViewRead(BaseModel):
    """Interaction Evidence View (Architect Session, S05E01):
    відповідь пацієнту складається з незалежних блоків довіри.
    v1 реалізує verified_interaction і prescription_history;
    patient_note - окремий сервіс на майбутнє.
    """

    patient_profile_id: int | None
    verified_interactions: list[DrugInteractionRead]
    prescription_history: list[PrescriptionHistoryEntryRead]

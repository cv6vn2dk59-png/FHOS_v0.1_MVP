from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.drug_interactions.domain.entities import (
    MAX_PATIENT_NOTE_LENGTH,
    InteractionSeverity,
)


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


class PatientInteractionNoteCreate(BaseModel):
    patient_profile_id: int | None = None
    substance_a: str = Field(min_length=1, max_length=255)
    substance_b: str = Field(min_length=1, max_length=255)
    note_text: str = Field(min_length=1, max_length=MAX_PATIENT_NOTE_LENGTH)


class PatientInteractionNoteRead(BaseModel):
    id: int
    patient_profile_id: int | None
    substance_a: str
    substance_b: str
    note_text: str
    unverified: bool
    created_at: datetime


class InteractionEvidenceViewRead(BaseModel):
    """Interaction Evidence View (Architect Session, S05E01):
    відповідь пацієнту складається з трьох незалежних блоків довіри,
    усі три реалізовано у v1: verified_interactions, prescription_history,
    patient_notes.
    """

    patient_profile_id: int | None
    verified_interactions: list[DrugInteractionRead]
    prescription_history: list[PrescriptionHistoryEntryRead]
    patient_notes: list[PatientInteractionNoteRead]

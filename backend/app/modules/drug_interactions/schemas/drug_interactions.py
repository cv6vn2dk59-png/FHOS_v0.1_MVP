from pydantic import BaseModel

from app.modules.drug_interactions.domain.entities import InteractionSeverity


class DrugInteractionRead(BaseModel):
    side_a: list[str]
    side_b: list[str]
    severity: InteractionSeverity
    description: str
    knowledge_source_id: str


class DrugInteractionCheckRead(BaseModel):
    patient_profile_id: int | None
    interactions: list[DrugInteractionRead]
    has_interactions: bool

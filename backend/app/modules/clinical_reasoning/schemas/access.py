from datetime import datetime
from pydantic import BaseModel, Field


class ConsentCreate(BaseModel):
    subject_patient_id: str
    granted_to_actor_id: str
    purpose_code: str
    resource_node_ids: list[str] = Field(min_length=1)
    allowed_operations: list[str] = Field(min_length=1)
    disclosure_level: str = "conclusion_only"
    allow_derivation: bool = True
    allow_disclosure_of_derivation: bool = True
    valid_from: datetime
    expires_at: datetime | None = None


class ConsentRead(ConsentCreate):
    id: int
    status: str
    revoked_at: datetime | None = None
    model_config = {"from_attributes": True}


class SharedNodeRequest(BaseModel):
    actor_id: str
    patient_ids: list[str] = Field(min_length=2)
    purpose_code: str


class SharedNodeRead(BaseModel):
    shared_nodes: dict[str, list[str]]

from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class ProvenanceInput(BaseModel):
    source_id: str
    source_version: str
    locator: str | None = None


class TemporalIntervalInput(BaseModel):
    earliest_start: datetime | None = None
    latest_start: datetime | None = None
    earliest_end: datetime | None = None
    latest_end: datetime | None = None
    precision: str = "unknown"
    timezone: str | None = None

    @model_validator(mode="after")
    def validate_order(self):
        if self.earliest_start and self.latest_start and self.earliest_start > self.latest_start:
            raise ValueError("earliest_start cannot be after latest_start")
        if self.earliest_end and self.latest_end and self.earliest_end > self.latest_end:
            raise ValueError("earliest_end cannot be after latest_end")
        return self


class ClinicalTimelineEventInput(BaseModel):
    id: str
    case_id: str
    kind: str
    label: str
    interval: TemporalIntervalInput
    provenance: list[ProvenanceInput] = Field(min_length=1)
    branch_ids: list[str] = Field(default_factory=list)
    context: dict[str, str] = Field(default_factory=dict)


class CausalTemporalLinkInput(BaseModel):
    id: str
    source_event_id: str
    target_event_id: str
    relation_type: str
    provenance: list[ProvenanceInput] = Field(min_length=1)
    minimum_lag_seconds: int | None = Field(default=None, ge=0)
    maximum_lag_seconds: int | None = Field(default=None, ge=0)
    confidence: float = Field(default=0.5, ge=0, le=1)


class TemporalCausalityRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    events: list[ClinicalTimelineEventInput] = Field(min_length=1)
    causal_links: list[CausalTemporalLinkInput] = Field(default_factory=list)


class TemporalCausalityRead(BaseModel):
    case_id: str
    ordered_event_ids: list[str]
    relations: list[dict]
    conflicts: list[dict]
    missing_evidence: list[dict]
    branch_assessments: list[dict]
    limitations: list[str]
    warnings: list[str]
    disclaimer: str = "Temporal precedence may support or weaken a causal hypothesis but does not establish causality."

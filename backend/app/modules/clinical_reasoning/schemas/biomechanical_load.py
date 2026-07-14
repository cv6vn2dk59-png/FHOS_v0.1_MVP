from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from .biomechanical_examination import ContextConstraintInput, HypothesisBranchInput, ProvenanceInput

class LoadExposureInput(BaseModel):
    id: str
    kind: str
    code: str
    magnitude: float | None = None
    duration_minutes: float | None = None
    frequency_per_week: float | None = None
    occurred_at: datetime | None = None
    body_region: str | None = None
    provenance: list[ProvenanceInput]
    context_constraints: list[ContextConstraintInput] = Field(default_factory=list)

class RecoveryCapacityInput(BaseModel):
    id: str
    sleep_quality: float | None = None
    recovery_hours: float | None = None
    baseline_capacity: float | None = None
    current_capacity: float | None = None
    limiting_factors: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceInput]
    context_constraints: list[ContextConstraintInput] = Field(default_factory=list)

class LoadResponseInput(BaseModel):
    id: str
    exposure_id: str
    symptom_change: float | None = None
    onset_delay_hours: float | None = None
    recovery_time_hours: float | None = None
    functional_change: str | None = None
    repeated_pattern: bool | None = None
    provenance: list[ProvenanceInput]
    context_constraints: list[ContextConstraintInput] = Field(default_factory=list)

class BiomechanicalLoadRequest(BaseModel):
    case_id: str
    branches: list[HypothesisBranchInput]
    exposures: list[LoadExposureInput]
    recovery: RecoveryCapacityInput | None = None
    responses: list[LoadResponseInput] = Field(default_factory=list)

class BiomechanicalLoadRead(BaseModel):
    case_id: str
    mismatches: list[dict]
    effects: list[dict]
    branch_assessments: list[dict]
    missing_evidence: list[dict]
    unassigned_exposure_ids: list[str]
    limitations: list[str]
    prohibited_conclusions: list[str]

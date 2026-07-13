from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ProvenanceInput(BaseModel):
    source_id: str
    source_version: str
    locator: str | None = None


class ContextConstraintInput(BaseModel):
    key: str
    operator: str
    value: Any


class HypothesisBranchInput(BaseModel):
    id: str
    case_id: str
    title: str
    description: str
    root_trigger_ids: list[str] = Field(default_factory=list)
    causal_domain: str
    branch_type: str
    node_ids: list[str] = Field(default_factory=list)
    edge_ids: list[str] = Field(default_factory=list)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    contradicting_fact_ids: list[str] = Field(default_factory=list)
    neutral_fact_ids: list[str] = Field(default_factory=list)
    missing_evidence_ids: list[str] = Field(default_factory=list)
    evidence_strength: str
    confidence: float
    status: str
    provenance: list[ProvenanceInput]
    context_constraints: list[ContextConstraintInput] = Field(default_factory=list)
    safety_critical: bool = False


class ExaminationFindingInput(BaseModel):
    id: str
    kind: str
    code: str
    result: str
    value: Any = None
    body_region: str | None = None
    laterality: str | None = None
    provenance: list[ProvenanceInput]
    context_constraints: list[ContextConstraintInput] = Field(default_factory=list)


class BiomechanicalExaminationRequest(BaseModel):
    case_id: str
    branches: list[HypothesisBranchInput]
    findings: list[ExaminationFindingInput]


class BiomechanicalExaminationRead(BaseModel):
    case_id: str
    effects: list[dict]
    branch_assessments: list[dict]
    missing_evidence: list[dict]
    safety_escalation_branch_ids: list[str]
    unassigned_finding_ids: list[str]
    limitations: list[str]
    prohibited_conclusions: list[str]

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


class BiomechanicalFactInput(BaseModel):
    id: str
    kind: str
    code: str
    value: str | float | bool
    laterality: str | None = None
    body_region: str | None = None
    provenance: list[ProvenanceInput]
    context_constraints: list[ContextConstraintInput] = Field(default_factory=list)


class BiomechanicsExpansionRequest(BaseModel):
    case_id: str
    facts: list[BiomechanicalFactInput]


class BiomechanicsExpansionRead(BaseModel):
    case_id: str
    branches: list[dict]
    relationships: list[dict]
    unassigned_fact_ids: list[str]
    red_flag_branch_ids: list[str]
    missing_evidence_ids: list[str]
    limitations: list[str]
    prohibited_conclusions: list[str]

from __future__ import annotations

from dataclasses import asdict

from app.modules.clinical_reasoning.domain.biomechanics import (
    BiomechanicalFact,
    BiomechanicalFactKind,
    HipComplexExpansionEngine,
)
from app.modules.clinical_reasoning.domain.causality import ContextConstraint, ProvenanceReference


class BiomechanicsService:
    def __init__(self) -> None:
        self.engine = HipComplexExpansionEngine()

    def expand_hip_complex(self, case_id: str, facts: list[dict]) -> dict:
        domain_facts = [
            BiomechanicalFact(
                id=fact["id"],
                kind=BiomechanicalFactKind(fact["kind"]),
                code=fact["code"],
                value=fact["value"],
                laterality=fact.get("laterality"),
                body_region=fact.get("body_region"),
                provenance=[ProvenanceReference(**item) for item in fact["provenance"]],
                context_constraints=[ContextConstraint(**item) for item in fact.get("context_constraints", [])],
            )
            for fact in facts
        ]
        result = self.engine.expand(case_id, domain_facts)
        return asdict(result)

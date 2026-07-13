from __future__ import annotations

from app.modules.clinical_reasoning.domain.branch_discrimination import (
    BranchDiscriminationEngine,
    EvidenceCandidate,
)
from app.modules.clinical_reasoning.domain.hypothesis_expansion import HypothesisBranch


class BranchDiscriminationService:
    def __init__(self, engine: BranchDiscriminationEngine | None = None) -> None:
        self.engine = engine or BranchDiscriminationEngine()

    def evaluate(
        self,
        case_id: str,
        branches: list[HypothesisBranch],
        candidates: list[EvidenceCandidate],
    ):
        return self.engine.evaluate(case_id, branches, candidates)

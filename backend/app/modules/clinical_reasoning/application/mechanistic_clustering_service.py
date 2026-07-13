from __future__ import annotations

from app.modules.clinical_reasoning.domain.hypothesis_expansion import HypothesisBranch
from app.modules.clinical_reasoning.domain.mechanistic_clustering import (
    BranchMechanisticProfile,
    MechanisticClusteringEngine,
)


class MechanisticClusteringService:
    def __init__(self, engine: MechanisticClusteringEngine | None = None) -> None:
        self.engine = engine or MechanisticClusteringEngine()

    def evaluate(self, case_id: str, branches: list[HypothesisBranch], profiles: list[BranchMechanisticProfile]):
        return self.engine.cluster(case_id, branches, profiles)

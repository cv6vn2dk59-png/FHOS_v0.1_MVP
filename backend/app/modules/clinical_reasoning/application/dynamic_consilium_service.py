from __future__ import annotations

from app.modules.clinical_reasoning.domain.dynamic_consilium import (
    BranchReview,
    ConsiliumRole,
    DynamicConsiliumEngine,
)
from app.modules.clinical_reasoning.domain.hypothesis_expansion import HypothesisBranch


class DynamicConsiliumService:
    def __init__(self, engine: DynamicConsiliumEngine | None = None) -> None:
        self.engine = engine or DynamicConsiliumEngine()

    def evaluate(
        self,
        case_id: str,
        branches: list[HypothesisBranch],
        roles: list[ConsiliumRole],
        reviews: list[BranchReview],
        cluster_branch_ids: list[list[str]] | None = None,
    ):
        return self.engine.evaluate(case_id, branches, roles, reviews, cluster_branch_ids or [])

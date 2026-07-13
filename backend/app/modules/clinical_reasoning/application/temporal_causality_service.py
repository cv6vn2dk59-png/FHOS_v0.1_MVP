from __future__ import annotations

from app.modules.clinical_reasoning.domain.temporal_causality import (
    CausalTemporalLink,
    ClinicalTimelineEvent,
    TemporalCausalityEngine,
)


class TemporalCausalityService:
    def __init__(self, engine: TemporalCausalityEngine | None = None) -> None:
        self.engine = engine or TemporalCausalityEngine()

    def evaluate(
        self,
        case_id: str,
        events: list[ClinicalTimelineEvent],
        causal_links: list[CausalTemporalLink],
    ):
        return self.engine.evaluate(case_id, events, causal_links)

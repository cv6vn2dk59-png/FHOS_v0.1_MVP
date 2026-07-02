"""
FHOS AI Operating System
Confidence Manager
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ConfidenceResult:
    score: float
    level: str
    missing_data: List[str]
    can_make_decision: bool


class ConfidenceManager:

    def evaluate(
        self,
        completeness: float,
        evidence_quality: float,
        expert_agreement: float,
    ) -> ConfidenceResult:

        score = (
            completeness * 0.4 +
            evidence_quality * 0.4 +
            expert_agreement * 0.2
        )

        if score >= 0.90:
            level = "Very High"

        elif score >= 0.75:
            level = "High"

        elif score >= 0.60:
            level = "Moderate"

        else:
            level = "Low"

        return ConfidenceResult(
            score=round(score, 2),
            level=level,
            missing_data=[],
            can_make_decision=score >= 0.75,
        )
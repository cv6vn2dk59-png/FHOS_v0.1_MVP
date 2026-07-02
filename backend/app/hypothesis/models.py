"""
FHOS Hypothesis Models

Hypothesis is not a diagnosis.
It is a possible explanation that must be tested.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClinicalHypothesis:

    id: str

    title: str

    status: str = "open"

    probability: float = 0.0

    supporting_evidence: list[str] = field(default_factory=list)

    contradicting_evidence: list[str] = field(default_factory=list)

    missing_data: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
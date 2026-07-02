"""
FHOS Evidence Analysis Models

EvidenceAnalysis evaluates a hypothesis against available evidence.
It does not make final decisions.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceAnalysis:

    id: str

    hypothesis_id: str

    status: str = "pending"

    supporting_evidence: list[str] = field(default_factory=list)

    contradicting_evidence: list[str] = field(default_factory=list)

    missing_data: list[str] = field(default_factory=list)

    strength: float = 0.0

    notes: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)
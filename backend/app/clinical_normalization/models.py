"""
FHOS Clinical Normalization Models

Clinical normalization converts raw evidence into cautious clinical statements.
It does not diagnose.
It does not add new facts.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedClinicalStatement:
    id: str
    evidence_id: str
    statement: str
    confidence: float = 0.5
    status: str = "needs_review"
    metadata: dict[str, Any] = field(default_factory=dict)
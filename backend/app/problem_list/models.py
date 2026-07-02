"""
FHOS Problem List Models
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClinicalProblem:

    id: str

    title: str

    status: str = "active"

    confidence: float = 0.0

    evidence: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
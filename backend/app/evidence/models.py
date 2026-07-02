"""
FHOS Evidence Models
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evidence:

    id: str

    source: str

    evidence_type: str

    title: str

    confidence: float = 1.0

    metadata: dict[str, Any] = field(default_factory=dict)
"""
FHOS Validation Models

ValidatedEvidence is information that passed validation.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidatedEvidence:
    id: str
    observation_id: str
    status: str = "unverified"
    normalized_content: str = ""
    confidence: float = 0.5
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
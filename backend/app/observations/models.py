"""
FHOS Observation Models

Observation is raw incoming information.
It is not yet validated evidence.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    id: str
    source: str
    observation_type: str
    raw_content: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
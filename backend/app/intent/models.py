"""
FHOS Intent Models

Intent is not a category.
Intent describes what the system should do next.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentResult:
    goal: str = "understand_request"
    confidence: float = 0.0

    requires_case: bool = False
    requires_medical_reasoning: bool = False
    requires_documents: bool = False
    requires_lab_results: bool = False
    requires_medication_profile: bool = False
    requires_follow_up: bool = False

    board_mode: str = "none"  # none | auto | required
    urgency: str = "unknown"  # unknown | low | normal | high | emergency

    missing_data: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
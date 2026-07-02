"""
FHOS Triage Models

Triage does not diagnose.
It checks urgency and missing critical information.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TriageResult:
    priority: str = "unknown"
    red_flags_checked: bool = False
    emergency: bool = False

    critical_questions: list[str] = field(default_factory=list)
    next_step: str = "collect_missing_information"

    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
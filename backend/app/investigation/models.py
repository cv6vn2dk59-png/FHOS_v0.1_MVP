"""
FHOS Investigation Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class InvestigationRevision:
    revision: int
    created_at: datetime
    event_id: str | None = None


@dataclass(slots=True)
class HistoryEntry:
    revision: int
    action: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ClinicalObjective:
    id: str
    name: str
    reason: str
    priority: int = 100
    completed: bool = False


@dataclass(slots=True)
class InformationGap:
    id: str
    objective_id: str
    code: str
    description: str
    priority: int = 100
    closed: bool = False


@dataclass(slots=True)
class QuestionCandidate:
    id: str
    gap_id: str
    rule_id: str
    text: str
    score: float = 0.0


@dataclass(slots=True)
class NextQuestion:
    id: str
    candidate_id: str
    text: str
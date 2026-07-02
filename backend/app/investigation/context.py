"""
FHOS Investigation Context
"""

from dataclasses import dataclass, field
from typing import Any

from app.investigation.models import (
    InvestigationRevision,
    HistoryEntry,
    ClinicalObjective,
    InformationGap,
    QuestionCandidate,
    NextQuestion,
)


@dataclass(slots=True)
class InvestigationContext:

    case_id: str

    revision: InvestigationRevision

    observations: list[dict] = field(default_factory=list)

    validated_evidence: list[dict] = field(default_factory=list)

    objectives: list[ClinicalObjective] = field(default_factory=list)

    gaps: list[InformationGap] = field(default_factory=list)

    question_candidates: list[QuestionCandidate] = field(default_factory=list)

    next_question: NextQuestion | None = None

    workflow: dict[str, Any] = field(default_factory=dict)

    triage: dict[str, Any] = field(default_factory=dict)

    history: list[HistoryEntry] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)
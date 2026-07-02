"""
FHOS Question Rule Models
"""

from dataclasses import dataclass


@dataclass(slots=True)
class QuestionRule:
    id: str
    gap_code: str
    question: str
    priority: int = 100
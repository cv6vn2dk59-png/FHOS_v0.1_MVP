"""
FHOS Clinical Case States
"""

from enum import Enum


class CaseState(str, Enum):
    NEW = "new"

    TRIAGE = "triage"

    INVESTIGATION = "investigation"

    WAITING_DATA = "waiting_data"

    MEDICAL_BOARD = "medical_board"

    DECISION = "decision"

    FOLLOW_UP = "follow_up"

    CLOSED = "closed"

    ARCHIVED = "archived"
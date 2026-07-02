"""
FHOS Case Matcher

Decides whether an event belongs to an existing Clinical Case
or should create a new case.

No medical logic here.
"""


class CaseMatcher:

    def match(self, event: dict, open_cases: list[dict]):

        if not open_cases:
            return {
                "matched": False,
                "case_id": None,
                "action": "create_new_case",
                "reason": "Немає відкритих клінічних випадків.",
            }

        return {
            "matched": False,
            "case_id": None,
            "action": "needs_review",
            "reason": "Потрібна оцінка релевантності події до відкритих випадків.",
        }
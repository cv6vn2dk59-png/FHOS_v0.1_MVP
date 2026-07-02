"""
FHOS Question Rules Registry

Question text lives here as data, not inside plugins.
"""

from app.question_rules.models import QuestionRule


QUESTION_RULES = [
    QuestionRule(
        id="rule_onset_time_001",
        gap_code="onset_time_unknown",
        question="Коли саме почалися симптоми?",
        priority=10,
    ),
    QuestionRule(
        id="rule_symptom_change_001",
        gap_code="symptom_dynamics_unknown",
        question="Симптоми посилюються, слабшають чи залишаються без змін?",
        priority=20,
    ),
    QuestionRule(
        id="rule_severity_001",
        gap_code="severity_unknown",
        question="Наскільки сильний симптом за шкалою від 0 до 10?",
        priority=30,
    ),
]


class QuestionRuleRegistry:

    def find_by_gap_code(self, gap_code: str):
        return [
            rule for rule in QUESTION_RULES
            if rule.gap_code == gap_code
        ]
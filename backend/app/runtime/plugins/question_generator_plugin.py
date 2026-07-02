"""
FHOS Question Generator Plugin
"""

from app.runtime.plugin import RuntimePlugin
from app.investigation.models import QuestionCandidate
from app.question_rules.registry import QuestionRuleRegistry


class QuestionGeneratorPlugin(RuntimePlugin):

    name = "question_generator"
    order = 50

    def __init__(self):
        self.registry = QuestionRuleRegistry()

    def execute(self, context):

        if context.question_candidates:
            return context

        counter = 1

        for gap in context.gaps:
            if gap.closed:
                continue

            rules = self.registry.find_by_gap_code(gap.code)

            for rule in rules:
                context.question_candidates.append(
                    QuestionCandidate(
                        id=f"candidate_{counter}",
                        gap_id=gap.id,
                        rule_id=rule.id,
                        text=rule.question,
                        score=1.0 / rule.priority,
                    )
                )

                counter += 1

        return context
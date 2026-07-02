"""
FHOS Question Selector Plugin
"""

from app.runtime.plugin import RuntimePlugin
from app.investigation.models import NextQuestion


class QuestionSelectorPlugin(RuntimePlugin):

    name = "question_selector"
    order = 60

    def execute(self, context):

        if not context.question_candidates:
            return context

        best = sorted(
            context.question_candidates,
            key=lambda item: item.score,
            reverse=True,
        )[0]

        context.next_question = NextQuestion(
            id=f"question_{context.revision.revision}",
            candidate_id=best.id,
            text=best.text,
        )

        return context
"""
FHOS Information Gap Plugin
"""

from app.runtime.plugin import RuntimePlugin
from app.investigation.models import InformationGap


class InformationGapPlugin(RuntimePlugin):

    name = "information_gap"
    order = 40

    def execute(self, context):

        if context.gaps:
            return context

        if not context.objectives:
            return context

        objective = context.objectives[0]

        context.gaps.append(
            InformationGap(
                id="gap_1",
                objective_id=objective.id,
                code="onset_time_unknown",
                description="Не відомий час початку симптомів.",
                priority=10,
            )
        )

        context.gaps.append(
            InformationGap(
                id="gap_2",
                objective_id=objective.id,
                code="symptom_dynamics_unknown",
                description="Не відомо, як змінюються симптоми з часом.",
                priority=20,
            )
        )

        context.gaps.append(
            InformationGap(
                id="gap_3",
                objective_id=objective.id,
                code="severity_unknown",
                description="Не відома інтенсивність симптомів.",
                priority=30,
            )
        )

        return context
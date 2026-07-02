from app.runtime.plugin import RuntimePlugin
from app.investigation.models import ClinicalObjective


class ObjectivePlugin(RuntimePlugin):

    name = "objective"

    order = 30

    def execute(self, context):

        if context.objectives:
            return context

        context.objectives.append(

            ClinicalObjective(

                id="objective_1",

                name="collect_clinical_information",

                reason="Недостатньо клінічних даних",

                priority=10,

            )

        )

        return context
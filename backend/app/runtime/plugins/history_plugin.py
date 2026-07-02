"""
FHOS History Plugin
"""

from app.runtime.plugin import RuntimePlugin
from app.investigation.history import HistoryManager


class HistoryPlugin(RuntimePlugin):

    name = "history"

    order = 100

    def execute(self, context):

        HistoryManager.append(

            context,

            "pipeline_completed",

            observations=len(context.observations),

            validated=len(context.validated_evidence),

        )

        return context
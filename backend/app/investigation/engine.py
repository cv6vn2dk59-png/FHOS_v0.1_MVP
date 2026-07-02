"""
FHOS Investigation Engine
"""

from app.investigation.context import InvestigationContext
from app.investigation.revision import RevisionFactory
from app.investigation.history import HistoryManager

from app.runtime.pipeline import RuntimePipeline

from app.runtime.plugins.observation_plugin import ObservationPlugin
from app.runtime.plugins.validation_plugin import ValidationPlugin
from app.runtime.plugins.objective_plugin import ObjectivePlugin
from app.runtime.plugins.information_gap_plugin import InformationGapPlugin
from app.runtime.plugins.question_generator_plugin import QuestionGeneratorPlugin
from app.runtime.plugins.question_selector_plugin import QuestionSelectorPlugin
from app.runtime.plugins.history_plugin import HistoryPlugin


class InvestigationEngine:

    def __init__(self):

        self.pipeline = RuntimePipeline()

        self.pipeline.register(ObservationPlugin())
        self.pipeline.register(ValidationPlugin())
        self.pipeline.register(ObjectivePlugin())
        self.pipeline.register(InformationGapPlugin())
        self.pipeline.register(QuestionGeneratorPlugin())
        self.pipeline.register(QuestionSelectorPlugin())
        self.pipeline.register(HistoryPlugin())

    def create_context(self, case_id: str):

        context = InvestigationContext(
            case_id=case_id,
            revision=RevisionFactory.first(),
        )

        HistoryManager.append(
            context,
            "context_created",
        )

        return context

    def step(
        self,
        context: InvestigationContext,
        event: dict,
    ):

        context.revision = RevisionFactory.next(
            context.revision,
            event_id=event.get("id"),
        )

        context.metadata["current_event"] = event

        context = self.pipeline.execute(context)

        context.metadata.pop("current_event", None)

        return context
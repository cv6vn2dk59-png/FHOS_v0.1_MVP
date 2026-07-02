"""
Runtime Pipeline Test
"""

from app.runtime.pipeline import RuntimePipeline
from app.runtime.plugin import RuntimePlugin

from app.investigation.engine import InvestigationEngine


class TestPlugin(RuntimePlugin):

    name = "test"

    order = 1

    def execute(self, context):

        context.metadata["pipeline"] = "executed"

        return context


engine = InvestigationEngine()

context = engine.create_context("case_1")

pipeline = RuntimePipeline()

pipeline.register(TestPlugin())

context = pipeline.execute(context)

print()

print(context.metadata)

print()
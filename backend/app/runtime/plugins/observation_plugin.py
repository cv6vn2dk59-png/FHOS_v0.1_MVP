"""
FHOS Observation Plugin
"""

from dataclasses import asdict

from app.runtime.plugin import RuntimePlugin
from app.observations.engine import ObservationEngine


class ObservationPlugin(RuntimePlugin):

    name = "observation"

    order = 10

    def __init__(self):

        self.engine = ObservationEngine()

    def execute(self, context):

        event = context.metadata.get("current_event")

        if event is None:
            return context

        observations = [
            asdict(item)
            for item in self.engine.build_from_event(event)
        ]

        context.observations.extend(observations)

        return context
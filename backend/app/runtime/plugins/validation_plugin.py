"""
FHOS Validation Plugin
"""

from dataclasses import asdict

from app.runtime.plugin import RuntimePlugin
from app.validation.engine import ValidationEngine


class ValidationPlugin(RuntimePlugin):

    name = "validation"

    order = 20

    def __init__(self):

        self.engine = ValidationEngine()

    def execute(self, context):

        if not context.observations:
            return context

        new_observations = []

        validated_ids = {
            item["observation_id"]
            for item in context.validated_evidence
        }

        for observation in context.observations:

            if observation["id"] not in validated_ids:

                new_observations.append(observation)

        if not new_observations:
            return context

        validated = [
            asdict(item)
            for item in self.engine.validate(new_observations)
        ]

        context.validated_evidence.extend(validated)

        return context
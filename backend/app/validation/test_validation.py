"""
Manual Observation -> Validation test
"""

from dataclasses import asdict

from app.observations.engine import ObservationEngine
from app.validation.engine import ValidationEngine


event = {
    "type": "user_request",
    "payload": {
        "text": "У мене болить голова третій день"
    },
}

observation_engine = ObservationEngine()
validation_engine = ValidationEngine()

observations = [
    asdict(item)
    for item in observation_engine.build_from_event(event)
]

validated_evidence = [
    asdict(item)
    for item in validation_engine.validate(observations)
]

print({
    "observations": observations,
    "validated_evidence": validated_evidence,
})
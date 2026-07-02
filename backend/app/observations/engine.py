"""
FHOS Observation Engine

Creates observations from incoming events.
Does not interpret medical meaning.
"""

from app.observations.models import Observation


class ObservationEngine:

    def build_from_event(self, event: dict):

        payload = event.get("payload", {})
        text = payload.get("text", "")

        if not text:
            return []

        observation = Observation(
            id="observation_1",
            source="user",
            observation_type="user_report",
            raw_content=text[:500],
            confidence=1.0,
            metadata={
                "event_type": event.get("type"),
            },
        )

        return [observation]
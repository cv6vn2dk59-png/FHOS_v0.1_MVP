"""
FHOS Evidence Engine

Creates evidence objects from incoming events.
Does not interpret medical meaning.
"""

from app.evidence.models import Evidence


class EvidenceEngine:

    def build_from_event(self, event: dict):

        payload = event.get("payload", {})
        text = payload.get("text", "")

        if not text:
            return []

        evidence = Evidence(
            id="evidence_1",
            source="user",
            evidence_type="user_report",
            title=text[:120],
            confidence=1.0,
            metadata={
                "event_type": event.get("type"),
            },
        )

        return [evidence]
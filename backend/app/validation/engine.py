"""
FHOS Validation Engine

Validates observations into evidence.
Does not diagnose.
Does not add new medical facts.
"""

from app.validation.models import ValidatedEvidence


class ValidationEngine:

    def validate(self, observations: list[dict]):

        results = []

        for index, item in enumerate(observations, start=1):
            content = item.get("raw_content", "")
            observation_id = item.get("id")

            if not content or not observation_id:
                continue

            evidence = ValidatedEvidence(
                id=f"validated_evidence_{index}",
                observation_id=observation_id,
                status="unverified",
                normalized_content=f"Користувач повідомляє: {content}",
                confidence=0.5,
                warnings=[
                    "Потребує клінічного уточнення."
                ],
                metadata={
                    "source": item.get("source"),
                    "observation_type": item.get("observation_type"),
                },
            )

            results.append(evidence)

        return results
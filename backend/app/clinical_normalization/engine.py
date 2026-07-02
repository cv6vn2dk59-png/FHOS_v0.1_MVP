"""
FHOS Clinical Normalization Engine

Converts evidence into cautious normalized clinical statements.
No diagnosis.
No disease names.
No hidden medical assumptions.
"""

from app.clinical_normalization.models import NormalizedClinicalStatement


class ClinicalNormalizationEngine:

    def normalize(self, evidence: list[dict]):

        statements = []

        for index, item in enumerate(evidence, start=1):
            title = item.get("title", "")
            evidence_id = item.get("id")

            if not title or not evidence_id:
                continue

            statement = NormalizedClinicalStatement(
                id=f"statement_{index}",
                evidence_id=evidence_id,
                statement=f"Користувач повідомляє: {title}",
                confidence=0.5,
                status="needs_review",
                metadata={
                    "source": item.get("source"),
                    "evidence_type": item.get("evidence_type"),
                },
            )

            statements.append(statement)

        return statements
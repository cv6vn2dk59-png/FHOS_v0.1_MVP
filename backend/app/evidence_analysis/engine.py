"""
FHOS Evidence Analysis Engine

Evaluates hypotheses against available evidence.
Does not make diagnosis.
Does not make treatment decisions.
"""

from app.evidence_analysis.models import EvidenceAnalysis


class EvidenceAnalysisEngine:

    def analyze(
        self,
        hypotheses: list[dict],
        evidence: list[dict],
    ):

        analyses = []

        for index, hypothesis in enumerate(hypotheses, start=1):

            supporting = hypothesis.get("supporting_evidence", [])
            missing = hypothesis.get("missing_data", [])

            analysis = EvidenceAnalysis(
                id=f"analysis_{index}",
                hypothesis_id=hypothesis.get("id"),
                status="incomplete",
                supporting_evidence=supporting,
                contradicting_evidence=[],
                missing_data=missing,
                strength=0.0,
                notes="Гіпотеза потребує додаткових даних для оцінки.",
                metadata={
                    "evidence_count": len(evidence),
                },
            )

            analyses.append(analysis)

        return analyses
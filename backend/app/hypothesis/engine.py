"""
FHOS Hypothesis Engine

Creates initial clinical hypotheses.

Does not diagnose.
Does not select specialists.
Only creates hypotheses that require verification.
"""

from app.hypothesis.models import ClinicalHypothesis


class HypothesisEngine:

    def build(
        self,
        problems: list[dict],
        evidence: list[dict],
    ):

        hypotheses = []

        for index, problem in enumerate(problems, start=1):

            hypothesis = ClinicalHypothesis(
                id=f"hypothesis_{index}",
                title="Потрібне клінічне уточнення",
                status="open",
                probability=0.0,
                supporting_evidence=problem.get("evidence", []),
                missing_data=[
                    "анамнез",
                    "фізикальний огляд",
                    "додаткові симптоми",
                ],
                metadata={
                    "problem_id": problem.get("id"),
                },
            )

            hypotheses.append(hypothesis)

        return hypotheses
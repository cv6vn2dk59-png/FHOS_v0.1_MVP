"""
FHOS Problem List Engine

Creates initial problem containers from normalized clinical statements.
Does not diagnose.
Does not name diseases.
"""

from app.problem_list.models import ClinicalProblem


class ProblemListEngine:

    def build_from_statements(
        self,
        statements: list[dict],
    ):

        problems = []

        for index, statement in enumerate(statements, start=1):
            problem = ClinicalProblem(
                id=f"problem_{index}",
                title="Потребує клінічного уточнення",
                status="active",
                confidence=0.5,
                evidence=[
                    statement.get("evidence_id")
                ],
                metadata={
                    "statement_id": statement.get("id"),
                    "statement": statement.get("statement"),
                },
            )

            problems.append(problem)

        return problems
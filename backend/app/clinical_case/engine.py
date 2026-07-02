"""
FHOS Clinical Case Engine

ClinicalCaseEngine does not know medical workflows.
It only creates a case container.
Workflow logic belongs to WorkflowEngine.
"""

from app.clinical_case.states import CaseState


class ClinicalCaseEngine:

    def create_case(
        self,
        title: str,
        patient_id: int | None = None,
        workflow_id: str | None = None,
    ):
        return {
            "patient_id": patient_id,
            "title": title,
            "workflow_id": workflow_id,
            "state": CaseState.NEW.value,
        }
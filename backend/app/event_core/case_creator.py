"""
FHOS Case Creator

Creates a Clinical Case container from an event and intent.
Does not save to database yet.
"""

from app.clinical_case.engine import ClinicalCaseEngine


class CaseCreator:

    def __init__(self):
        self.case_engine = ClinicalCaseEngine()

    def create_from_event(self, event: dict, intent: dict):

        payload = event.get("payload", {})
        text = payload.get("text", "")

        title = self._make_title(text)

        return self.case_engine.create_case(
            title=title,
            patient_id=payload.get("patient_id"),
            workflow_id="clinical_investigation_default",
        )

    def _make_title(self, text: str):

        if not text:
            return "Новий клінічний випадок"

        return text[:80]
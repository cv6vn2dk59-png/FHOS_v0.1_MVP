"""
FHOS AI Operating System
Report Builder
"""


class ReportBuilder:

    def build(self, capability, context, result):

        return {
            "title": "FHOS AI Medical Board Report",
            "capability": capability,
            "patient_context": context.get("patient"),
            "clinical_context": context.get("clinical_context"),
            "laboratory_context": context.get("laboratory_context"),
            "consensus": result.get("summary"),
            "confidence": result.get("confidence"),
            "warnings": result.get("warnings"),
            "experts": result.get("experts"),
            "safety": context.get("safety"),
        }
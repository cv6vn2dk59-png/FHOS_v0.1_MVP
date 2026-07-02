"""
FHOS AI Operating System
Context Builder
"""


class ContextBuilder:

    def build_context(self, request: str, capability_name: str):

        return {
            "request": request,
            "capability": capability_name,
            "patient": None,
            "clinical_context": {
                "known_conditions": [],
                "medications": [],
                "symptoms": [],
            },
            "laboratory_context": {
                "requested_focus": [],
                "status": "not_loaded",
            },
            "documents": [],
            "safety": {
                "final_decision": "не приймати клінічних рішень без лікаря",
                "missing_data": [
                    "вік",
                    "стать",
                    "симптоми",
                    "тривалість скарг",
                    "температура",
                    "ліки",
                    "результати огляду або аналізів",
                ],
            },
        }
"""
FHOS Clinical Investigation Engine

This module does not provide medical answers.
It starts a structured clinical investigation.
"""


class ClinicalInvestigationEngine:

    def start(self, request: str):

        return {
            "status": "started",
            "request": request,
            "principle": "FHOS проводить клінічне розслідування, а не дає швидку відповідь.",
            "steps": [
                {
                    "step": 1,
                    "name": "Clarify problem",
                    "description": "Уточнити головну скаргу, тривалість, вік, стать та небезпечні симптоми.",
                },
                {
                    "step": 2,
                    "name": "Build hypotheses",
                    "description": "Побудувати список можливих причин без передчасного висновку.",
                },
                {
                    "step": 3,
                    "name": "Check red flags",
                    "description": "Визначити, чи є ознаки термінового звернення до лікаря.",
                },
                {
                    "step": 4,
                    "name": "Collect missing data",
                    "description": "Сформувати перелік даних, яких бракує.",
                },
                {
                    "step": 5,
                    "name": "Expand context",
                    "description": "Підтягнути лише релевантні дані з історії пацієнта.",
                },
                {
                    "step": 6,
                    "name": "Build medical board",
                    "description": "Динамічно залучити потрібних цифрових експертів.",
                },
            ],
            "output": {
                "conclusion": None,
                "reason": "Висновок не формується до завершення розслідування.",
            },
        }
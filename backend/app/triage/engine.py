"""
FHOS Triage Engine

Checks urgency and defines the next critical questions.
Does not diagnose.
"""


from app.triage.models import TriageResult


class TriageEngine:

    def assess(
        self,
        intent: dict,
        problems: list[dict],
        evidence: list[dict],
    ):

        result = TriageResult(
            priority="normal",
            red_flags_checked=False,
            emergency=False,
            critical_questions=[
                "Скільки вам років?",
                "Коли саме почалися симптоми?",
                "Чи є температура?",
                "Чи була втрата свідомості?",
                "Чи є слабкість, оніміння, порушення мовлення або зору?",
                "Який зараз артеріальний тиск?",
            ],
            next_step="ask_critical_questions",
            notes="Потрібно уточнити небезпечні симптоми перед подальшим аналізом.",
        )

        if intent.get("urgency") == "emergency":
            result.priority = "emergency"
            result.emergency = True
            result.next_step = "recommend_urgent_medical_attention"
            result.notes = "Є ознаки потенційно небезпечного стану."

        return result
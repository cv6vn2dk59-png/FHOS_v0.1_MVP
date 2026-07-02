"""
FHOS Intent Engine

Determines what the system should do next.
Does not diagnose.
Does not choose specialties.
"""

from app.intent.models import IntentResult


class IntentEngine:

    def analyze(self, request: str) -> IntentResult:
        text = request.lower()

        result = IntentResult(
            goal="understand_request",
            confidence=0.5,
            requires_case=True,
            requires_medical_reasoning=True,
            board_mode="auto",
            urgency="normal",
            missing_data=[
                "вік",
                "стать",
                "тривалість",
                "основні симптоми",
            ],
            next_actions=[
                "створити або знайти клінічний випадок",
                "уточнити ключові дані",
                "перевірити небезпечні симптоми",
            ],
        )

        if any(word in text for word in ["терміново", "швидка", "втрата свідомості", "задуха"]):
            result.urgency = "emergency"
            result.next_actions.insert(0, "негайно перевірити red flags")

        if any(word in text for word in ["аналіз", "ттг", "гемоглобін", "феритин"]):
            result.requires_lab_results = True
            result.next_actions.append("перевірити лабораторні дані")

        if any(word in text for word in ["pdf", "мрт", "кт", "рентген", "узд"]):
            result.requires_documents = True
            result.next_actions.append("перевірити медичні документи або зображення")

        if any(word in text for word in ["ліки", "препарат", "ібупрофен", "спазмалгон"]):
            result.requires_medication_profile = True
            result.next_actions.append("перевірити ліки, алергії та взаємодії")

        return result
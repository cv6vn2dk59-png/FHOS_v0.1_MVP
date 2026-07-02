"""
FHOS AI Operating System
Consensus Engine
"""


class ConsensusEngine:

    def build(self, opinions):

        active_opinions = [
            item for item in opinions
            if item.get("opinion") is not None
        ]

        silent_experts = [
            item.get("expert")
            for item in opinions
            if item.get("opinion") is None
        ]

        if not active_opinions:
            return {
                "status": "no_consensus",
                "summary": "Немає достатньо експертних думок для висновку.",
                "experts": opinions,
                "active_experts": [],
                "silent_experts": silent_experts,
                "confidence": 0.0,
                "warnings": [
                    "Недостатньо даних для формування висновку."
                ],
            }

        confidence_values = [
            item.get("confidence", 0.0)
            for item in active_opinions
        ]

        average_confidence = round(
            sum(confidence_values) / len(confidence_values),
            2
        )

        active_experts = [
            item.get("expert")
            for item in active_opinions
        ]

        warnings = []

        if "Devils Advocate" in active_experts:
            warnings.append(
                "Devils Advocate вимагає перевірки альтернативних пояснень."
            )

        if silent_experts:
            warnings.append(
                "Не всі експерти надали думку."
            )

        return {
            "status": "completed",
            "summary": "Сформовано попередній консенсус Medical Decision Board.",
            "experts": opinions,
            "active_experts": active_experts,
            "silent_experts": silent_experts,
            "confidence": average_confidence,
            "warnings": warnings,
        }
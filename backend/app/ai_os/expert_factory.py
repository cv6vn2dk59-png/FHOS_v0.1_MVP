"""
FHOS AI Operating System
Expert Factory
"""

from app.ai_os.expert_registry import expert_registry


class ExpertFactory:

    def create(self, domain_name: str):

        profile = expert_registry.get(domain_name)

        if profile is None:
            profile = self._create_generic_profile(domain_name)
            expert_registry.register(domain_name, profile)

        return {
            "name": domain_name,
            "title": profile["title"],
            "status": profile.get("status", "auto_created"),
            "role": profile["role"],
            "priority": profile["priority"],
            "opinion": profile["default_opinion"],
            "confidence": profile["default_confidence"],
            "recommendations": profile["recommendations"],
        }

    def _create_generic_profile(self, domain_name: str):

        return {
            "title": domain_name,
            "status": "auto_created",
            "role": f"Автоматично створений експерт для напрямку: {domain_name}",
            "priority": "normal",
            "default_opinion": f"Потрібен первинний аналіз напрямку: {domain_name}.",
            "default_confidence": 0.50,
            "recommendations": [
                "Уточнити дані для аналізу.",
                "Визначити релевантні клінічні джерела.",
            ],
        }
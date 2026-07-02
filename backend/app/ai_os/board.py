"""
FHOS AI Operating System
Medical Decision Board
"""

from app.ai_os.expert_factory import ExpertFactory


class MedicalBoard:

    def __init__(self):
        self.factory = ExpertFactory()

    def discuss(self, board):
        opinions = []

        for domain in board:
            expert = self.factory.create(domain)

            opinions.append(
                {
                    "expert": expert["title"],
                    "domain": expert["name"],
                    "status": expert["status"],
                    "role": expert["role"],
                    "priority": expert["priority"],
                    "opinion": expert["opinion"],
                    "confidence": expert["confidence"],
                    "recommendations": expert["recommendations"],
                }
            )

        return opinions
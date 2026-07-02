"""
FHOS Clinical Event Router

Decides what should happen with every incoming event.
No medical logic here.
"""


class ClinicalEventRouter:

    def route(self, event: dict):

        event_type = event.get("type")

        return {
            "event_type": event_type,
            "action": "determine_case",
            "status": "pending",
        }
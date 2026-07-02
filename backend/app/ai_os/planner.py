"""
Task Planner
"""

from .registry import CAPABILITIES


class Planner:

    def plan(self, request: str):

        request = request.lower()

        if "ттг" in request or "аналіз" in request:
            return CAPABILITIES["laboratory_analysis"]

        if "ліки" in request:
            return CAPABILITIES["drug_interaction"]

        if "перелом" in request:
            return CAPABILITIES["orthopedic_case"]

        return CAPABILITIES["laboratory_analysis"]
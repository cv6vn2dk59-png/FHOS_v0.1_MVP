"""
FHOS AI Operating System
Expert Registry
"""


class ExpertRegistry:

    def __init__(self):
        self.experts = {}

    def register(self, domain_name: str, profile: dict):
        self.experts[domain_name] = profile

    def get(self, domain_name: str):
        return self.experts.get(domain_name)

    def exists(self, domain_name: str):
        return domain_name in self.experts


expert_registry = ExpertRegistry()
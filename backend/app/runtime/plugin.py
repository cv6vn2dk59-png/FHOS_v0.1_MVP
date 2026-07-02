"""
FHOS Runtime Plugin Base
"""

from abc import ABC, abstractmethod

from app.investigation.context import InvestigationContext


class RuntimePlugin(ABC):

    name = "plugin"
    order = 100

    @abstractmethod
    def execute(self, context: InvestigationContext) -> InvestigationContext:
        """
        Execute plugin and return updated context.
        """
        raise NotImplementedError()
"""
FHOS Runtime Pipeline
"""

from app.investigation.context import InvestigationContext
from app.runtime.registry import PluginRegistry


class RuntimePipeline:

    def __init__(self):

        self.registry = PluginRegistry()

    def register(self, plugin):

        self.registry.register(plugin)

    def execute(self, context: InvestigationContext):

        for plugin in self.registry.plugins():

            context = plugin.execute(context)

        return context
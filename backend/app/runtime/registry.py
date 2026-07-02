"""
FHOS Runtime Registry
"""

from app.runtime.plugin import RuntimePlugin


class PluginRegistry:

    def __init__(self):

        self._plugins: list[RuntimePlugin] = []

    def register(self, plugin: RuntimePlugin):

        self._plugins.append(plugin)

        self._plugins.sort(key=lambda x: x.order)

    def plugins(self):

        return self._plugins
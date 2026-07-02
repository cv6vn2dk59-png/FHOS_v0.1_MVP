"""
Base LLM Provider
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:
        pass
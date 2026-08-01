"""Base provider abstract class."""

from abc import ABC, abstractmethod
from typing import Any

from app.models import ProviderResponse


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tool_config: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> ProviderResponse:
        """Send messages to the LLM and return a unified response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: System-level instruction for the model.
            tool_config: Optional Bedrock tool configuration.

        Returns:
            ProviderResponse with success status and model output.
        """
        ...

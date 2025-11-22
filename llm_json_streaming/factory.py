from typing import Optional
from .base import LLMJsonProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider

def create_provider(provider_name: str, **kwargs) -> LLMJsonProvider:
    """
    Factory function to create an LLM provider instance.

    Args:
        provider_name: The name of the provider ("openai", "anthropic").
        **kwargs: Arguments to pass to the provider constructor (e.g. api_key).

    Returns:
        An instance of LLMJsonProvider.

    Raises:
        ValueError: If the provider name is not supported.
    """
    name = provider_name.lower()
    
    if name == "openai":
        return OpenAIProvider(**kwargs)
    elif name == "anthropic" or name == "claude":
        return AnthropicProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")

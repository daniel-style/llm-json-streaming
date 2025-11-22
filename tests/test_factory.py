import pytest
from llm_json_streaming import create_provider
from llm_json_streaming.providers import OpenAIProvider, AnthropicProvider

def test_create_provider_openai():
    provider = create_provider("openai", api_key="dummy")
    assert isinstance(provider, OpenAIProvider)

def test_create_provider_anthropic():
    provider = create_provider("anthropic", api_key="dummy")
    assert isinstance(provider, AnthropicProvider)

def test_create_provider_claude_alias():
    provider = create_provider("claude", api_key="dummy")
    assert isinstance(provider, AnthropicProvider)

def test_create_provider_invalid():
    with pytest.raises(ValueError):
        create_provider("invalid", api_key="dummy")

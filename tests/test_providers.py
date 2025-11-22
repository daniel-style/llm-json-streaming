import pytest
from llm_json_streaming.providers import OpenAIProvider

def test_provider_instantiation():
    # Just testing import and init
    provider = OpenAIProvider(api_key="dummy")
    assert provider is not None


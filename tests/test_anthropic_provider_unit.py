import types
import pytest
from pydantic import BaseModel

from llm_json_streaming.providers import AnthropicProvider


class DummySchema(BaseModel):
    value: str


def _bind_async_generator(provider, func):
    return types.MethodType(func, provider)


@pytest.mark.asyncio
async def test_structured_outputs_path_for_new_models():
    provider = AnthropicProvider(api_key="dummy")

    async def structured_stub(self, *args, **kwargs):
        yield {"path": "structured"}

    async def prefill_stub(self, *args, **kwargs):
        yield {"path": "prefill"}

    provider._stream_structured_outputs = _bind_async_generator(provider, structured_stub)
    provider._stream_prefill_json = _bind_async_generator(provider, prefill_stub)

    chunks = []
    async for chunk in provider.stream_json("prompt", DummySchema, model="claude-sonnet-4.5"):
        chunks.append(chunk)

    assert chunks == [{"path": "structured"}]


@pytest.mark.asyncio
async def test_prefill_path_for_legacy_models():
    provider = AnthropicProvider(api_key="dummy")

    async def structured_stub(self, *args, **kwargs):
        yield {"path": "structured"}

    async def prefill_stub(self, *args, **kwargs):
        yield {"path": "prefill"}

    provider._stream_structured_outputs = _bind_async_generator(provider, structured_stub)
    provider._stream_prefill_json = _bind_async_generator(provider, prefill_stub)

    chunks = []
    async for chunk in provider.stream_json("prompt", DummySchema, model="claude-3-5-sonnet-20240620"):
        chunks.append(chunk)

    assert chunks == [{"path": "prefill"}]


@pytest.mark.asyncio
async def test_use_structured_outputs_override_flag():
    provider = AnthropicProvider(api_key="dummy")

    async def structured_stub(self, *args, **kwargs):
        yield {"path": "structured"}

    async def prefill_stub(self, *args, **kwargs):
        yield {"path": "prefill"}

    provider._stream_structured_outputs = _bind_async_generator(provider, structured_stub)
    provider._stream_prefill_json = _bind_async_generator(provider, prefill_stub)

    chunks = []
    async for chunk in provider.stream_json(
        "prompt",
        DummySchema,
        model="claude-3-5-sonnet-20240620",
        use_structured_outputs=True,
    ):
        chunks.append(chunk)

    assert chunks == [{"path": "structured"}]


@pytest.mark.asyncio
async def test_structured_outputs_disabled_for_custom_base_url():
    provider = AnthropicProvider(api_key="dummy", base_url="https://proxy.example.com")

    async def structured_stub(self, *args, **kwargs):
        yield {"path": "structured"}

    async def prefill_stub(self, *args, **kwargs):
        yield {"path": "prefill"}

    provider._stream_structured_outputs = _bind_async_generator(provider, structured_stub)
    provider._stream_prefill_json = _bind_async_generator(provider, prefill_stub)

    chunks = []
    async for chunk in provider.stream_json("prompt", DummySchema, model="claude-sonnet-4.5"):
        chunks.append(chunk)

    assert chunks == [{"path": "prefill"}]


@pytest.mark.asyncio
async def test_structured_override_respected_for_custom_base_url():
    provider = AnthropicProvider(api_key="dummy", base_url="https://proxy.example.com")

    async def structured_stub(self, *args, **kwargs):
        yield {"path": "structured"}

    async def prefill_stub(self, *args, **kwargs):
        yield {"path": "prefill"}

    provider._stream_structured_outputs = _bind_async_generator(provider, structured_stub)
    provider._stream_prefill_json = _bind_async_generator(provider, prefill_stub)

    chunks = []
    async for chunk in provider.stream_json(
        "prompt",
        DummySchema,
        model="claude-sonnet-4.5",
        use_structured_outputs=True,
    ):
        chunks.append(chunk)

    assert chunks == [{"path": "structured"}]


def test_schema_instruction_contains_schema_details():
    provider = AnthropicProvider(api_key="dummy")
    instruction = provider._build_schema_instruction(DummySchema)
    assert "### JSON generation rules" in instruction
    assert '• "value"' in instruction
    assert "(string, required)" in instruction
    assert "Respond with a SINGLE JSON object" in instruction


def test_prefill_system_prompt_emphasizes_braces():
    provider = AnthropicProvider(api_key="dummy")
    system_prompt = provider._build_prefill_system_prompt(DummySchema)
    assert "Begin your reply with '{'" in system_prompt
    assert "end with '}'" in system_prompt
    assert "required field" in system_prompt


def test_prefill_stub_uses_first_field():
    provider = AnthropicProvider(api_key="dummy")
    stub = provider._build_prefill_stub(DummySchema)
    assert stub.startswith("{")
    assert '"value"' in stub


def test_structured_output_prefix_detection():
    provider = AnthropicProvider(api_key="dummy")
    assert provider._supports_structured_outputs("sonnet-4.5-latest")
    assert provider._supports_structured_outputs("claude-sonnet-4-5-preview")
    assert not provider._supports_structured_outputs("foo-sonnet-4.5")


def test_detect_prefill_prefix_finds_last_assistant_stub():
    provider = AnthropicProvider(api_key="dummy")
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "{\n  \"name\":"},
    ]
    assert provider._detect_prefill_prefix(messages) == '{\n  "name":'


def test_detect_prefill_prefix_returns_empty_without_assistant_stub():
    provider = AnthropicProvider(api_key="dummy")
    messages = [{"role": "user", "content": "hello"}]
    assert provider._detect_prefill_prefix(messages) == ""


def test_merge_prefill_snapshot_adds_prefix_when_missing():
    provider = AnthropicProvider(api_key="dummy")
    combined = provider._merge_prefill_snapshot(' "x"}', '{\n  "value":')
    assert combined == '{\n  "value": "x"}'


def test_merge_prefill_snapshot_passthrough_when_prefix_present():
    provider = AnthropicProvider(api_key="dummy")
    snapshot = '{\n  "value":"x"}'
    combined = provider._merge_prefill_snapshot(snapshot, '{\n  "value":')
    assert combined == snapshot


def test_safe_parse_json_validates_schema():
    provider = AnthropicProvider(api_key="dummy")
    parsed = provider._safe_parse_json('{"value":"hi"}', DummySchema)
    assert isinstance(parsed, DummySchema)
    assert parsed.value == "hi"
    assert provider._safe_parse_json("not-json", DummySchema) is None


def test_looks_like_json_payload_heuristic():
    provider = AnthropicProvider(api_key="dummy")
    assert provider._looks_like_json_payload('{"value":')
    assert provider._looks_like_json_payload("[1, 2")
    assert not provider._looks_like_json_payload("Plain text response")


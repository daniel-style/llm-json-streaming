# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a unified Python library for streaming structured JSON outputs from OpenAI and Anthropic (Claude) models. The library abstracts provider differences and offers a consistent interface for streaming JSON data and parsed Pydantic objects.

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_providers.py
```

### Testing
The project uses pytest with pytest-asyncio for async testing. Tests are organized in:
- `tests/test_providers.py` - Base provider tests
- `tests/test_factory.py` - Factory pattern tests
- `tests/test_openai_integration.py` - OpenAI-specific tests
- `tests/test_anthropic_integration.py` - Anthropic-specific tests
- `tests/test_anthropic_provider_unit.py` - Anthropic unit tests
- `tests/test_mock_provider.py` - Mock provider for testing

## Architecture

### Core Components

1. **Base Provider** ([`llm_json_streaming/base.py`](llm_json_streaming/base.py))
   - `LLMJsonProvider` abstract class defining the streaming interface
   - Provides utility methods for JSON parsing and validation
   - Key methods:
     - `_safe_parse_json()`: Attempts to parse accumulated JSON using the schema
     - `_get_best_partial_json()`: Returns both parsed object and raw JSON text

2. **Factory Pattern** ([`llm_json_streaming/factory.py`](llm_json_streaming/factory.py))
   - `create_provider()` function for instantiating providers
   - Supports "openai", "anthropic", or "claude" as provider names

3. **Provider Implementations**
   - **OpenAI Provider** ([`llm_json_streaming/providers/openai_provider.py`](llm_json_streaming/providers/openai_provider.py))
     - Uses `client.beta.chat.completions.stream` with structured outputs
     - Default model: `gpt-4o-2024-08-06`

   - **Anthropic Provider** ([`llm_json_streaming/providers/anthropic_provider.py`](llm_json_streaming/providers/anthropic_provider.py))
     - Dual strategy: Structured Outputs for new models, prefill for legacy
     - Structured Outputs for Claude Sonnet 4.5+ and Opus 4.1+
     - Prefill strategy for older Claude models
     - Uses specialized streaming classes:
       - `StructuredOutputStreamer` ([`llm_json_streaming/providers/anthropic_structured.py`](llm_json_streaming/providers/anthropic_structured.py))
       - `PrefillJSONStreamer` ([`llm_json_streaming/providers/anthropic_prefill.py`](llm_json_streaming/providers/anthropic_prefill.py))

### Streaming Interface

All providers implement the `stream_json()` method that yields dictionaries with:
- `partial_object`: Current best parsed Pydantic object (for structured outputs) or dictionary (for prefill mode)
- `delta`: Real-time text updates during streaming
- `final_object`: Complete, validated Pydantic model when streaming finishes
- `partial_json`: Current accumulated JSON text string
- `final_json`: Complete JSON text string when streaming finishes

**Best Practice**: Use `partial_object` for real-time UI updates as it provides the most reliable partial parsing of the accumulated JSON text. Note that prefill mode returns partial objects as dictionaries, while structured outputs return Pydantic model instances.

### Configuration

Set API keys in environment variables:
- `OPENAI_API_KEY` and `OPENAI_BASE_URL`
- `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`

## Key Design Patterns

1. **Strategy Pattern**: Anthropic provider dynamically chooses between structured outputs and prefill strategies based on model capabilities
2. **Factory Pattern**: Centralized provider instantiation with consistent interface
3. **Template Method**: Base provider defines streaming workflow, concrete providers implement specifics
4. **Async Generators**: All streaming operations use async generators for memory-efficient output streaming

## Model Detection

Anthropic provider automatically detects structured output capability through model name patterns containing:
- `claude-sonnet-4.5*` or `sonnet-4.5*`
- `claude-opus-4.1*` or `opus-4.1*`

## Prefill Mode JSON Repair

The prefill strategy for older Claude models includes enhanced partial object support:

- **JSON Repair Integration**: Uses `json_repair` library to fix incomplete JSON during streaming
- **Partial Object Support**: Provides real-time partial objects as dictionaries during streaming (not just Pydantic models)
- **Graceful Degradation**: Falls back to raw JSON text when repair fails
- **Final Validation**: Still attempts full schema validation for the final output

This enables older Claude models (like Claude 3 Haiku) to provide real-time partial object updates that were previously only available with structured outputs.
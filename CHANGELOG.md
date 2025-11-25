# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-11-25

### Fixed
- 🔧 **GitHub Actions CI/CD Improvements**:
  - Fixed deprecated actions/upload-artifact and actions/download-artifact v3 usage
  - Upgraded to artifact actions v4 for future compatibility
  - Resolved YAML syntax errors in release workflow
  - Fixed boolean input value formatting for GitHub Actions

### Changed
- 🚀 **Enhanced Release Process**:
  - Improved automated publishing workflow
  - Better environment configuration for PyPI publishing
  - Enhanced changelog generation from git tags

## [0.1.0] - 2024-11-25

### Added
- 🎉 **Initial Release** - Unified LLM JSON streaming library
- ✨ **Multi-provider Support** - OpenAI, Anthropic (Claude), and Google Gemini
- 📦 **PyPI Package** - Published as `llm-json-streaming` on PyPI
- 🧪 **Test PyPI Support** - Pre-release testing on Test PyPI
- 📚 **Comprehensive Documentation** - README, API Reference, and examples

#### Core Features
- **Unified Interface**: Single API for all supported providers
- **Streaming JSON Output**: Real-time structured data streaming
- **Pydantic Integration**: Automatic schema validation and type safety
- **Partial Object Support**: Progressive JSON parsing during streaming
- **JSON Repair**: Automatic repair for incomplete JSON (Anthropic & Google)

#### Provider Implementations
- **OpenAI Provider**
  - Native structured outputs via beta API
  - Default model: `gpt-4o-2024-08-06`
  - Full streaming support with schema validation

- **Anthropic Provider**
  - **Automatic Mode Detection**: Chooses strategy based on model capabilities
  - **Structured Outputs Mode**: For Claude Sonnet 4.5+ and Opus 4.1+
  - **Prefill Strategy**: For older Claude models with JSON repair
  - Default model: `claude-3-5-sonnet-20240620`
  - Support for `claude-sonnet-4.5*` and `claude-opus-4.1*` auto-detection

- **Google Gemini Provider**
  - Native structured outputs via `response_mime_type="application/json"`
  - Default model: `gemini-2.5-flash`
  - Built-in JSON repair for enhanced partial object support
  - Direct Pydantic schema integration

#### API Design
- **Factory Pattern**: `create_provider()` function with provider selection
- **Async Streaming**: `stream_json()` method yielding progressive chunks
- **Chunk Types**:
  - `partial_object`: Real-time parsed objects
  - `delta`: Raw text increments
  - `final_object`: Complete validated Pydantic objects
  - `partial_json` / `final_json`: Raw JSON strings

#### Development & Testing
- **Comprehensive Test Suite**: Unit tests, integration tests, and end-to-end tests
- **Mock Provider**: For testing without API calls
- **Error Handling**: Robust error recovery and type safety
- **Development Tools**: Pre-commit hooks, type checking, and linting

#### Documentation
- **README**: Quick start guide and usage examples
- **API Reference**: Complete method documentation
- **Troubleshooting Guide**: Common issues and solutions
- **Test Results**: Detailed testing report and validation

#### Package Information
- **Version**: 0.1.0
- **Python**: 3.9+ support
- **Dependencies**: Automatically managed
- **License**: MIT License
- **Install Size**: ~21KB (wheel), ~71KB (source)

#### Quality Assurance
- **PyPI Published**: https://pypi.org/project/llm-json-streaming/
- **Test PyPI**: https://test.pypi.org/project/llm-json-streaming/
- **Validation**: 100% basic functionality tests passed
- **Provider Testing**: Multi-provider compatibility verified

---

## Installation

```bash
# From PyPI (recommended)
pip install llm-json-streaming

# Using uv
uv add llm-json-streaming

# From Test PyPI (pre-release)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ llm-json-streaming
```

## Quick Example

```python
import asyncio
from pydantic import BaseModel
from llm_json_streaming import create_provider

class UserProfile(BaseModel):
    name: str
    age: int
    bio: str

async def main():
    provider = create_provider("openai")  # or "anthropic", "google"

    async for chunk in provider.stream_json(
        "Generate a user profile",
        UserProfile
    ):
        if "partial_object" in chunk:
            print(f"Partial: {chunk['partial_object']}")

        if "final_object" in chunk:
            final = chunk["final_object"]
            print(f"Final: {final.name}, {final.age}")
            break

asyncio.run(main())
```

---

## Support

- **GitHub Issues**: https://github.com/daniel-style/llm-json-streaming/issues
- **Documentation**: https://github.com/daniel-style/llm-json-streaming#readme
- **API Reference**: https://github.com/daniel-style/llm-json-streaming/blob/main/API_REFERENCE.md
- **PyPI**: https://pypi.org/project/llm-json-streaming/

## Contributors

- **Daniel Wu** - Creator and maintainer

---

*Note: This changelog covers the initial release. Future versions will follow the same format with detailed change tracking.*
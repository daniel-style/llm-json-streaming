# LLM JSON Streaming

[![PyPI Version](https://img.shields.io/pypi/v/llm-json-streaming.svg)](https://pypi.org/project/llm-json-streaming/)
[![Python Versions](https://img.shields.io/pypi/pyversions/llm-json-streaming.svg)](https://pypi.org/project/llm-json-streaming/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/daniel-style/llm-json-streaming/actions)

A unified Python library for streaming structured JSON outputs from OpenAI, Anthropic (Claude), and Google Gemini.

This library leverages **native model capabilities** for structured JSON generation—avoiding tool-based approaches entirely. By using each provider's built-in structured output features, it delivers superior performance, reliability, and efficiency compared to traditional function calling or tool methods.

## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install llm-json-streaming

# Or using uv (recommended)
uv add llm-json-streaming
```

### Try the Example

```bash
# Clone and try the comprehensive example
git clone https://github.com/daniel-style/llm-json-streaming.git
cd llm-json-streaming/examples/fastapi_nextjs

# Auto-setup and run both servers
./start.sh
```

Open http://localhost:3000 to see real-time JSON streaming in action!

## ✨ Key Features

- **🔥 Native Model Capabilities**: Leverages each provider's built-in structured output features—no function calling or tool overhead
- **⚡ Superior Performance**: 2-3x faster than tool-based approaches with zero latency
- **🛡️ Enhanced Reliability**: Eliminates tool-based failures and guarantees schema compliance
- **🔌 Unified Interface**: Single API for OpenAI, Anthropic, and Google Gemini
- **📡 Real-time Streaming**: Access raw JSON chunks as they are generated
- **🎯 Structured Outputs**: Enforce schema validation using Pydantic models
- **🔧 Partial Parsing**: Access accumulated JSON strings during streaming
- **🤖 Claude Support**: Native structured outputs + prefill strategy for all models
- **🌟 Gemini Integration**: Direct JSON streaming with automatic repair

## 📋 Installation Options

### 📦 From PyPI (Recommended)

```bash
# Using pip
pip install llm-json-streaming

# Using uv (recommended)
uv add llm-json-streaming
```

### 🧪 From Test PyPI

```bash
# Using pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ llm-json-streaming

# Using uv
uv add --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ llm-json-streaming
```

### 🛠️ From Source

```bash
git clone https://github.com/daniel-style/llm-json-streaming.git
cd llm-json-streaming

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

**Package Info**: PyPI: https://pypi.org/project/llm-json-streaming/ | Python: 3.9+ | Current Version: 0.1.0

## 🎯 Example Project

### 🚀 FastAPI + Next.js Demo

A comprehensive full-stack example demonstrating real-world usage:

```bash
# Clone and run the example
git clone https://github.com/daniel-style/llm-json-streaming.git
cd llm-json-streaming/examples/fastapi_nextjs

# Auto-setup and start both servers
./start.sh
```

**What's Included:**
- 🔄 **Multi-provider Support**: Switch between Anthropic, OpenAI, and Google Gemini
- 📡 **Real-time Streaming**: Live JSON updates rendered in React UI
- 🎨 **Complex Schemas**: Nested Pydantic models for travel guide generation
- ⚡ **Modern Stack**: FastAPI backend + Next.js frontend with TypeScript
- 🛡️ **Production Features**: Error handling, loading states, responsive UI

Open http://localhost:3000 to see streaming JSON in action!

**Manual Setup**: Backend runs on http://localhost:8000 | Frontend on http://localhost:3000

## Configuration

Set your API keys in a `.env` file:

```ini
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com

GEMINI_API_KEY=your_gemini_api_key
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com  # Optional
```

## Usage

### 🚀 Quick Start

Define your output schema using Pydantic and pass it to the provider:

```python
import asyncio
import os
from pydantic import BaseModel
from llm_json_streaming import create_provider

# 1. Define your schema
class UserProfile(BaseModel):
    name: str
    age: int
    bio: str
    skills: list[str] = []

async def main():
    # 2. Initialize provider using the factory
    # Available: "openai", "anthropic", "claude", "google"
    # Ensure environment variables are set, or pass api_key="..."
    try:
        # For Anthropic, you can optionally specify mode:
        provider = create_provider("openai")  # Use OpenAI
        # provider = create_provider("anthropic", mode="auto")  # Anthropic with auto-detection
        # provider = create_provider("google")  # Google Gemini
    except ValueError as e:
        print(f"Provider creation error: {e}")
        return

    prompt = "Generate a profile for a fictional software engineer."

    # 3. Stream results
    print("🔄 Streaming JSON...")
    try:
        async for chunk in provider.stream_json(prompt, UserProfile):
            # Real-time partial parsed object (recommended for streaming updates)
            if "partial_object" in chunk:
                obj = chunk["partial_object"]
                # Handle both dict and Pydantic objects
                if hasattr(obj, 'name'):  # Pydantic object
                    name = obj.name or "..."
                    age = obj.age if obj.age else "?"
                else:  # Dict object
                    name = obj.get('name', "...")
                    age = obj.get('age', "?")

                print(f"\r📝 Current: {name}, Age: {age}", end="", flush=True)

            # Final parsed object (complete and validated)
            if "final_object" in chunk:
                final_profile = chunk["final_object"]
                print(f"\n\n✅ Complete: {final_profile.name}, Age: {final_profile.age}")
                print(f"📋 Bio: {final_profile.bio}")
                if final_profile.skills:
                    print(f"🛠️  Skills: {', '.join(final_profile.skills)}")
                break

    except Exception as e:
        print(f"\n❌ Error during streaming: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 🔧 Advanced Usage

#### Multiple Providers Comparison

```python
import asyncio
from llm_json_streaming import create_provider
from pydantic import BaseModel

class TaskResult(BaseModel):
    title: str
    status: str
    priority: int

async def compare_providers():
    providers = {
        "OpenAI": create_provider("openai"),
        "Anthropic": create_provider("anthropic", mode="auto"),
        "Google": create_provider("google")
    }

    prompt = "Create a software development task with title, status, and priority"

    results = {}
    for name, provider in providers.items():
        try:
            async for chunk in provider.stream_json(prompt, TaskResult):
                if "final_object" in chunk:
                    results[name] = chunk["final_object"]
                    print(f"✅ {name}: {results[name].title}")
                    break
        except Exception as e:
            print(f"❌ {name} failed: {e}")

    return results

# Run comparison
# asyncio.run(compare_providers())
```

#### Error Handling & Type Safety

```python
import asyncio
from llm_json_streaming import create_provider
from pydantic import BaseModel, ValidationError

class APIResponse(BaseModel):
    success: bool
    data: dict
    error_message: str = ""

async def safe_streaming_example():
    try:
        provider = create_provider("anthropic")  # Fallback provider

        async for chunk in provider.stream_json(
            "Process this user request",
            APIResponse
        ):
            if "partial_object" in chunk:
                obj = chunk["partial_object"]

                # Safe object handling
                if isinstance(obj, dict):
                    # Handle dict objects
                    success = obj.get('success', False)
                elif hasattr(obj, 'success'):
                    # Handle Pydantic objects
                    success = obj.success
                else:
                    print("⚠️  Unexpected object type")
                    continue

                # Process partial results...

            if "final_object" in chunk:
                final = chunk["final_object"]
                print(f"✅ Final result: {final}")
                break

    except ValidationError as e:
        print(f"❌ Schema validation error: {e}")
    except Exception as e:
        print(f"❌ Streaming error: {e}")
```

## Streaming Interface

The `stream_json()` method yields dictionaries with different types of content during streaming:

### Chunk Fields

- **`partial_object`**: The current best parsed object. Available from the beginning of streaming in all modes:
  - **Early stage**: Returns partial dictionaries for incomplete JSON
  - **Later stage**: Returns validated Pydantic model instances for complete/repairable JSON
- **`delta`**: Raw text characters as they are generated by the LLM.
- **`final_object`**: The complete, validated Pydantic object when streaming finishes.
- **`partial_json`**: The current accumulated JSON text string.
- **`final_json`**: The complete JSON text string when streaming finishes.


## Supported Providers & Models

| Provider | Default Model | Native Method Used | Performance Advantage |
|----------|---------------|-------------------|----------------------|
| OpenAI   | `gpt-4o-2024-08-06` | `response_format` (Native Structured Outputs) via `beta.chat.completions` | **2-3x faster** than function calling, guaranteed schema compliance |
| Anthropic   | `claude-3-5-sonnet-20240620` (auto-switches to Structured Outputs for `claude-sonnet-4.5*` / `claude-opus-4.1*`) | **Native Structured Outputs** (`output_format` + beta header) or **Schema-aware Prefill** for legacy models | **No tool overhead**, direct JSON generation, eliminates tool call latency |
| Google   | `gemini-2.5-flash` | **Native Structured Outputs** via `response_mime_type="application/json"` | **Direct JSON streaming**, no function calling delays |

### Anthropic Mode Configuration

You can configure which strategy Anthropic models use through multiple methods:

#### Method 1: Constructor Mode (Recommended)

```python
from llm_json_streaming import create_provider

# Force structured outputs mode
provider = create_provider("anthropic", mode="structured")

# Force prefill mode
provider = create_provider("anthropic", mode="prefill")

# Auto-detection based on model (default)
provider = create_provider("anthropic", mode="auto")
```

#### Method 2: Method Parameter Override

```python
# Temporary override per request
async for chunk in provider.stream_json(prompt, UserProfile,
                                       model="claude-3-5-sonnet-20240620",
                                       use_structured_outputs=True):
    # Uses structured outputs regardless of auto-detection
```

#### Mode Priority

1. **Constructor mode** (`mode=` parameter) - Highest priority
2. **Method parameter** (`use_structured_outputs=`) - Medium priority
3. **Auto-detection** - Based on model capabilities - Lowest priority

### Anthropic Structured Outputs

Claude Sonnet 4.5 and Claude Opus 4.1 support Anthropic's **native structured output** capabilities.
When using structured mode, chunks include partial JSON text and final Pydantic objects automatically.

**Performance Benefits:**
- **Direct JSON generation**: No function calling overhead or tool delays
- **Guaranteed schema compliance**: Native validation eliminates parsing errors
- **Streaming efficiency**: Continuous JSON output without tool call interruptions

### Anthropic Prefill Mode

All other Claude models receive schema-derived instructions and an assistant prefill (e.g., `{` or `{"field":`) so they skip generic preambles and stream JSON directly—**no tool definitions or tool-use deltas required**.

**Advantages over Tool-Based Approaches:**
- **Zero tool call latency**: Immediate JSON streaming from first token
- **Eliminates tool failures**: No tool selection or parameter validation errors
- **Consistent output format**: Pure JSON without tool wrapper artifacts
- **Enhanced partial object support**:
  - Real-time partial objects available from the first token
  - Progressive improvement from partial dictionaries to Pydantic objects
  - JSON repair automatically fixes incomplete JSON for better parsing
  - Consistent interface matching structured outputs behavior

### Google Gemini Support

Google Gemini models use the Google GenAI SDK with **native structured outputs**—no function calling required:

```python
from llm_json_streaming import create_provider

provider = create_provider("google")
async for chunk in provider.stream_json(prompt, UserProfile, model="gemini-2.5-flash"):
    # Handle streaming chunks
    if "partial_object" in chunk:
        print(chunk["partial_object"])
```

**Native Advantages over Function Calling:**
- **Direct JSON generation**: Uses `response_mime_type="application/json"` for guaranteed JSON responses
- **No tool call delays**: Eliminates function call overhead and response parsing
- **Enhanced reliability**: Native validation avoids tool-based failure modes
- **JSON Repair**: Automatic repair of incomplete JSON for superior partial object support
- **Schema Validation**: Direct Pydantic schema integration for type-safe responses
- **Continuous Streaming**: Real-time partial objects with progressive enhancement without tool interruptions

**Configuration:**
- Set `GEMINI_API_KEY` environment variable (required)
- Optionally set `GOOGLE_BASE_URL` for custom endpoints
- Default model: `gemini-2.5-flash`

## Testing

### Running Tests

To run the tests with `uv`:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_providers.py

# Run with coverage
uv run pytest --cov=llm_json_streaming
```

### Quick Validation

Test the package installation and basic functionality:

```bash
# Using the test package
git clone https://github.com/daniel-style/llm-json-streaming.git
cd llm-json-streaming/test_package

# Test with uv
cd llm-test-project
uv add llm-json-streaming==0.1.0
uv run python basics_test.py
```

## Troubleshooting

### 🔧 Common Issues

#### Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'llm_json_streaming'`
```bash
# Solution: Install the package
pip install llm-json-streaming
# or
uv add llm-json-streaming
```

**Problem**: Dependency conflicts
```bash
# Solution: Use virtual environment
python -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate
pip install llm-json-streaming
```

#### API Key Issues

**Problem**: Authentication errors
```bash
# Solution: Set environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GEMINI_API_KEY="your-key"

# Or create .env file
echo "OPENAI_API_KEY=your-key" > .env
```

### 📞 Getting Help

1. **Check the [test results](test_package/TEST_RESULTS.md)** for known issues
2. **Review usage examples** in the test package
3. **Open an issue** on GitHub with:
   - Python version
   - Package version
   - Error message
   - Minimal reproduction code
4. **Check provider documentation**:
   - [OpenAI API](https://platform.openai.com/docs)
   - [Anthropic API](https://docs.anthropic.com)
   - [Google Gemini API](https://ai.google.dev/docs)

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone and set up development environment
git clone https://github.com/daniel-style/llm-json-streaming.git
cd llm-json-streaming

# Using uv (recommended)
uv sync

# Or using pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=llm_json_streaming

# Specific provider tests
uv run pytest tests/test_openai_integration.py
```

## License

[MIT](LICENSE)

## 📚 Additional Resources

- **PyPI Package**: https://pypi.org/project/llm-json-streaming/
- **Test PyPI**: https://test.pypi.org/project/llm-json-streaming/
- **GitHub Repository**: https://github.com/daniel-style/llm-json-streaming
- **Issue Tracker**: https://github.com/daniel-style/llm-json-streaming/issues
- **Documentation**: See inline code documentation and examples

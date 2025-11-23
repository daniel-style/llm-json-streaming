# LLM JSON Streaming

A unified Python library for streaming structured JSON outputs from OpenAI and Anthropic (Claude).

This library abstracts the differences between providers' structured output APIs and provides a consistent interface to stream JSON data and parsed Pydantic objects.

## Features

- **Unified Interface**: Use a single API to interact with OpenAI and Anthropic.
- **JSON Streaming**: Access raw JSON chunks as they are generated (`delta`).
- **Structured Outputs**: Enforce schema validation using Pydantic models.
- **Partial Parsing**: Access accumulated JSON strings during streaming.
- **Claude Structured Outputs**: Automatically upgrades Claude Sonnet 4.5 / Opus 4.1 requests to Anthropic's JSON outputs for guaranteed schemas.
- **Claude Prefill Strategy**: Older Claude models avoid tool calls entirely—schema-aware prefilling keeps responses JSON-only while still streaming deltas.

## Installation

This project is managed with `uv`.

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-json-streaming.git
cd llm-json-streaming

# Install dependencies
uv sync
```

## Configuration

Set your API keys in a `.env` file:

```ini
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

## Usage

Define your output schema using Pydantic and pass it to the provider.

```python
import asyncio
from pydantic import BaseModel
from llm_json_streaming import create_provider

# 1. Define your schema
class UserProfile(BaseModel):
    name: str
    age: int
    bio: str

async def main():
    # 2. Initialize provider using the factory
    # Available: "openai", "anthropic"
    # Ensure environment variables are set, or pass api_key="..."
    try:
        provider = create_provider("openai")
    except ValueError as e:
        print(e)
        return

    prompt = "Generate a profile for a fictional software engineer."

    # 3. Stream results
    print("Streaming JSON...")
    try:
        async for chunk in provider.stream_json(prompt, UserProfile):
            # Real-time text update
            if "delta" in chunk:
                print(chunk["delta"], end="", flush=True)
            
            # Final parsed object
            if "final_object" in chunk:
                user_profile = chunk["final_object"]
                print(f"\n\nParsed: {user_profile.name}, {user_profile.age}")
    except Exception as e:
        print(f"\nError during streaming: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Supported Providers & Models

| Provider | Default Model | Method Used |
|----------|---------------|-------------|
| OpenAI   | `gpt-4o-2024-08-06` | `response_format` (Structured Outputs) via `beta.chat.completions` |
| Anthropic   | `claude-3-5-sonnet-20240620` (auto-switches to Structured Outputs for `claude-sonnet-4.5*` / `claude-opus-4.1*`) | Prefill JSON streaming for legacy models, Structured Outputs (`output_format` + beta header) for Sonnet 4.5 / Opus 4.1 |

### Anthropic Structured Outputs

Claude Sonnet 4.5 and Claude Opus 4.1 support Anthropic's structured output beta.  
`AnthropicProvider.stream_json` detects these models (or you can pass `use_structured_outputs=True`) and sends the `output_format` schema plus the `structured-outputs-2025-11-13` beta header, so chunks include partial JSON text and final Pydantic objects automatically.

### Anthropic Prefill Mode

All other Claude models now receive schema-derived instructions and an assistant prefill (e.g., `{` or `{"field":`) so they skip generic preambles and stream JSON directly—no tool definitions or tool-use deltas required.

## Testing

To run the tests with `uv`:

```bash
uv run pytest
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)

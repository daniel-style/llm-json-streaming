# API Reference

## Core API

### `create_provider(provider_name: str, **kwargs) -> LLMJsonProvider`

Factory function to create a provider instance.

**Parameters:**
- `provider_name` (str): Provider name. Supported values:
  - `"openai"` - OpenAI provider
  - `"anthropic"` or `"claude"` - Anthropic provider
  - `"google"` - Google Gemini provider
- `**kwargs`: Additional provider-specific parameters
  - `mode` (str, Anthropic only): `"auto"`, `"structured"`, or `"prefill"`
  - `api_key` (str): Override environment variable
  - `base_url` (str): Custom API endpoint
  - `model` (str): Custom model name

**Returns:**
- `LLMJsonProvider`: Provider instance

**Raises:**
- `ValueError`: If provider name is not supported

```python
from llm_json_streaming import create_provider

# OpenAI provider
provider = create_provider("openai")

# Anthropic with specific mode
provider = create_provider("anthropic", mode="structured")

# Custom API key
provider = create_provider("openai", api_key="your-key")
```

### `LLMJsonProvider`

Abstract base class for all providers.

#### Methods

##### `stream_json(prompt: str, schema: Type[BaseModel], **kwargs) -> AsyncGenerator[Dict[str, Any], None]`

Stream JSON output from LLM with schema validation.

**Parameters:**
- `prompt` (str): Input prompt for the LLM
- `schema` (Type[BaseModel]): Pydantic model for output validation
- `**kwargs`: Additional parameters
  - `model` (str): Override default model
  - `temperature` (float): Sampling temperature (0.0-2.0)
  - `max_tokens` (int): Maximum output tokens
  - `use_structured_outputs` (bool, Anthropic): Force mode override

**Yields:**
- `Dict[str, Any]`: Streaming chunk with the following keys:
  - `"partial_object"`: Current best parsed object (dict or BaseModel)
  - `"delta"`: Raw text increment since last chunk
  - `"final_object"`: Complete validated Pydantic object (last chunk only)
  - `"partial_json"`: Accumulated JSON text string
  - `"final_json"`: Complete JSON string (last chunk only)

```python
import asyncio
from pydantic import BaseModel
from llm_json_streaming import create_provider

class Task(BaseModel):
    title: str
    status: str

async def stream_example():
    provider = create_provider("anthropic")

    async for chunk in provider.stream_json("Create a task", Task):
        if "partial_object" in chunk:
            print(f"Partial: {chunk['partial_object']}")

        if "final_object" in chunk:
            final = chunk["final_object"]
            print(f"Final: {final.title}")
            break
```

## Provider-Specific APIs

### OpenAI Provider (`OpenAIProvider`)

**Default Model:** `gpt-4o-2024-08-06`

**Features:**
- Native structured outputs via OpenAI's beta API
- Automatic schema conversion
- Streaming support

**Configuration:**
```python
# Environment variables
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Or in code
provider = create_provider("openai", api_key="key", base_url="url")
```

**Supported Parameters:**
- `model`: Default `"gpt-4o-2024-08-06"`
- `temperature`: 0.0-2.0
- `max_tokens`: Maximum tokens
- `base_url`: Custom endpoint

### Anthropic Provider (`AnthropicProvider`)

**Default Model:** `claude-3-5-sonnet-20240620`

**Modes:**
- `"auto"` (default): Automatic mode detection based on model
- `"structured"`: Force structured outputs mode
- `"prefill"`: Force prefill strategy

**Model Detection:**
Models containing these patterns automatically use structured outputs:
- `claude-sonnet-4.5*` or `sonnet-4.5*`
- `claude-opus-4.1*` or `opus-4.1*`

**Configuration:**
```python
# Environment variables
ANTHROPIC_API_KEY=your-key
ANTHROPIC_BASE_URL=https://api.anthropic.com

# In code
provider = create_provider("anthropic", mode="auto")
```

**Supported Parameters:**
- `mode`: `"auto"`, `"structured"`, or `"prefill"`
- `model`: Default `"claude-3-5-sonnet-20240620"`
- `temperature`: 0.0-1.0
- `max_tokens`: Maximum tokens

### Google Gemini Provider (`GoogleProvider`)

**Default Model:** `gemini-2.5-flash`

**Features:**
- Native structured outputs
- JSON repair for partial objects
- Schema validation

**Configuration:**
```python
# Environment variables
GEMINI_API_KEY=your-key
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com

# In code
provider = create_provider("google", api_key="key")
```

**Supported Parameters:**
- `model`: Default `"gemini-2.5-flash"`
- `temperature`: 0.0-2.0
- `max_output_tokens`: Maximum output tokens

## Streaming Interface

### Chunk Structure

Each yielded chunk contains different fields based on streaming state:

```python
{
    "partial_object": Union[dict, BaseModel],  # Current best parsed object
    "delta": str,                              # Raw text increment
    "partial_json": str,                       # Accumulated JSON text
    "final_object": BaseModel,                 # Complete validated object (end)
    "final_json": str                          # Complete JSON text (end)
}
```

### Usage Patterns

#### Real-time Updates

```python
async for chunk in provider.stream_json(prompt, Model):
    if "partial_object" in chunk:
        obj = chunk["partial_object"]
        # Handle both dict and BaseModel objects
        if hasattr(obj, 'field_name'):  # Pydantic
            value = obj.field_name
        else:  # Dict
            value = obj.get('field_name')

        update_ui(value)
```

#### Character-by-Character Display

```python
async for chunk in provider.stream_json(prompt, Model):
    if "delta" in chunk:
        print(chunk["delta"], end="", flush=True)
```

#### Final Result Processing

```python
async for chunk in provider.stream_json(prompt, Model):
    if "final_object" in chunk:
        final = chunk["final_object"]
        # Process complete, validated object
        save_result(final)
        break
```

## Error Handling

### Common Exceptions

```python
try:
    async for chunk in provider.stream_json(prompt, Model):
        # Process chunks
        pass
except ValueError as e:
    # Invalid provider or parameters
    print(f"Configuration error: {e}")
except Exception as e:
    # API or streaming error
    print(f"Streaming error: {e}")
```

### Type Safety

```python
from pydantic import ValidationError

try:
    # Schema validation happens automatically
    final = chunk["final_object"]
except ValidationError as e:
    print(f"Schema validation failed: {e}")
```

## Models and Schemas

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class User(BaseModel):
    name: str
    age: int
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

# Complex nested models
class Project(BaseModel):
    id: str
    title: str
    owner: User
    tasks: List[Task]
```

### Schema Conversion

The library automatically converts Pydantic models to provider-specific schemas:

- **OpenAI**: JSON Schema format
- **Anthropic**: JSON Schema format
- **Google**: Direct Pydantic model support

### Validation

- **Input validation**: Pydantic model validation
- **Output validation**: Automatic schema enforcement
- **Type conversion**: Automatic type handling
- **Error reporting**: Detailed validation errors

## Advanced Usage

### Custom Models

```python
# Override default models
provider = create_provider("openai", model="gpt-4o-mini")
provider = create_provider("anthropic", model="claude-3-haiku-20240307")
provider = create_provider("google", model="gemini-1.5-pro")
```

### Batch Processing

```python
async def process_multiple():
    provider = create_provider("openai")
    tasks = ["task1", "task2", "task3"]

    for task in tasks:
        async for chunk in provider.stream_json(task, TaskModel):
            if "final_object" in chunk:
                results.append(chunk["final_object"])
                break
```

### Error Recovery

```python
async def robust_streaming(prompt, model):
    providers = ["openai", "anthropic", "google"]

    for provider_name in providers:
        try:
            provider = create_provider(provider_name)
            async for chunk in provider.stream_json(prompt, model):
                if "final_object" in chunk:
                    return chunk["final_object"]
        except Exception as e:
            print(f"Provider {provider_name} failed: {e}")
            continue

    raise Exception("All providers failed")
```

## Performance Considerations

### Streaming Efficiency

- Use `partial_object` for real-time updates
- Process `delta` only for character-by-character display
- Cache `final_object` for repeated access

### Memory Management

```python
# Memory-efficient streaming
async for chunk in provider.stream_json(large_prompt, LargeModel):
    if "partial_object" in chunk:
        # Process incrementally, don't store all chunks
        process_partial(chunk["partial_object"])

    if "final_object" in chunk:
        # Only store final result
        final = chunk["final_object"]
        break
```

### Rate Limits

- OpenAI: RPM and TPM limits
- Anthropic: RPM limits
- Google: QPM limits

Implement backoff strategies for rate limit handling.
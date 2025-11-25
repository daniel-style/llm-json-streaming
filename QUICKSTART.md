# Quick Start Guide

Get up and running with `llm-json-streaming` in minutes!

## 🚀 1. Installation

```bash
# Install with pip
pip install llm-json-streaming

# Or with uv (recommended)
uv add llm-json-streaming
```

## 🔑 2. Set Up API Keys

Create a `.env` file or set environment variables:

```bash
# Required for OpenAI
OPENAI_API_KEY=your_openai_key_here

# Required for Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Required for Google Gemini
GEMINI_API_KEY=your_gemini_key_here
```

## 💻 3. Basic Usage

```python
import asyncio
from pydantic import BaseModel
from llm_json_streaming import create_provider

# Define your output schema
class Task(BaseModel):
    title: str
    status: str
    priority: int

async def main():
    # Create a provider (OpenAI, Anthropic, or Google)
    provider = create_provider("openai")  # Try "anthropic" or "google"

    # Stream structured JSON output
    async for chunk in provider.stream_json(
        "Create a software development task with title, status, and priority",
        Task
    ):
        if "partial_object" in chunk:
            # Real-time updates (shows progress)
            obj = chunk["partial_object"]
            if hasattr(obj, 'title') and obj.title:
                print(f"📝 Task: {obj.title}")

        if "final_object" in chunk:
            # Complete, validated result
            task = chunk["final_object"]
            print(f"\n✅ Complete Task:")
            print(f"   Title: {task.title}")
            print(f"   Status: {task.status}")
            print(f"   Priority: {task.priority}")
            break

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 4. Try Different Providers

```python
# OpenAI (GPT-4o)
openai_provider = create_provider("openai")

# Anthropic (Claude) - with auto mode detection
anthropic_provider = create_provider("anthropic", mode="auto")

# Google Gemini
gemini_provider = create_provider("google")

# Test all providers
providers = [openai_provider, anthropic_provider, gemini_provider]
for i, provider in enumerate(providers):
    print(f"\n🔧 Testing provider {i+1}...")
    # Use the same streaming code with each provider
```

## 🛠️ 5. Advanced Features

### Error Handling
```python
async def safe_streaming():
    try:
        async for chunk in provider.stream_json(prompt, Model):
            if "final_object" in chunk:
                return chunk["final_object"]
    except Exception as e:
        print(f"Error: {e}")
        return None
```

### Type Safety
```python
async for chunk in provider.stream_json(prompt, Task):
    if "partial_object" in chunk:
        obj = chunk["partial_object"]

        # Handle both dict and Pydantic objects safely
        if hasattr(obj, 'title'):  # Pydantic object
            title = obj.title
        else:  # Dict object
            title = obj.get('title', 'Unknown')
```

### Custom Models
```python
from typing import List, Optional

class User(BaseModel):
    name: str
    email: str
    projects: List[str] = []
    active: Optional[bool] = True

# Use complex schemas
async for chunk in provider.stream_json(
    "Generate a developer profile",
    User
):
    if "final_object" in chunk:
        user = chunk["final_object"]
        print(f"User: {user.name}")
        print(f"Projects: {len(user.projects)}")
```

## 📚 Next Steps

- 📖 **Read the full documentation**: [README.md](README.md)
- 🔍 **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- 🧪 **Testing Guide**: [test_package/README.md](test_package/README.md)
- 🐛 **Troubleshooting**: [README.md#troubleshooting](README.md#troubleshooting)
- 📋 **Examples**: [test_package/USAGE_EXAMPLE.py](test_package/USAGE_EXAMPLE.py)

## 🎯 Common Use Cases

### Data Processing
```python
class DataAnalysis(BaseModel):
    insights: List[str]
    confidence: float
    summary: str

async for chunk in provider.stream_json(
    "Analyze this sales data and provide insights",
    DataAnalysis
):
    # Real-time data analysis
    pass
```

### Content Generation
```python
class BlogPost(BaseModel):
    title: str
    content: str
    tags: List[str]

async for chunk in provider.stream_json(
    "Write a blog post about Python programming",
    BlogPost
):
    # Real-time content generation
    pass
```

### Configuration Management
```python
class AppConfig(BaseModel):
    database_url: str
    debug_mode: bool
    max_connections: int

async for chunk in provider.stream_json(
    "Generate a production app configuration",
    AppConfig
):
    # Real-time config generation
    pass
```

## 🔗 Need Help?

- **GitHub Issues**: [Report bugs or request features](https://github.com/daniel-style/llm-json-streaming/issues)
- **Documentation**: [Full documentation](README.md)
- **Examples**: [Complete examples](test_package/USAGE_EXAMPLE.py)

---

**Happy streaming! 🎉**
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''

---

## 🐛 Bug Description

<!-- A clear and concise description of what the bug is -->

## 🔢 Steps to Reproduce

<!-- Please provide detailed steps to reproduce the issue -->

1.
2.
3.

## 🎯 Expected Behavior

<!-- A clear and concise description of what you expected to happen -->

## 📱 Current Behavior

<!-- A clear and concise description of what actually happens -->

## 💻 Environment

- **OS**: [e.g. macOS 12.0, Ubuntu 20.04]
- **Python Version**: [e.g. 3.9, 3.10, 3.11]
- **Package Version**: [e.g. 0.1.0]
- **Dependencies**: [e.g. openai==1.0.0, anthropic==0.25.0]

## 📋 Code Example

<!-- Please provide a minimal code example that reproduces the issue -->

```python
import asyncio
from pydantic import BaseModel
from llm_json_streaming import create_provider

class TestModel(BaseModel):
    field: str

async def reproduce_bug():
    provider = create_provider("openai")
    # Your code here
    pass

asyncio.run(reproduce_bug())
```

## 📝 Error Messages/Logs

<!-- Please copy and paste any relevant error messages or logs -->

```
# Paste error messages here
```

## 🔍 Additional Context

<!-- Add any other context about the problem here -->

## 📎 Attachments

<!-- Upload any relevant files, screenshots, etc. -->
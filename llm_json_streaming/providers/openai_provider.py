import os
from typing import Any, AsyncGenerator, Dict, Type
from pydantic import BaseModel
from openai import AsyncOpenAI
from ..base import LLMJsonProvider

class OpenAIProvider(LLMJsonProvider):
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url
        )

    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str = "gpt-4o-2024-08-06",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams JSON from OpenAI using Structured Outputs via Chat Completions.
        Uses client.beta.chat.completions.stream which is more compatible with proxies
        than the /v1/responses endpoint, while still supporting Structured Outputs.
        """
        
        # Use beta.chat.completions.stream for structured outputs
        async with self.client.beta.chat.completions.stream(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
            **kwargs
        ) as stream:
            async for event in stream:
                if event.type == "content.delta":
                    yield {
                        "delta": event.delta,
                        "partial_json": event.snapshot,
                        "partial_object": event.parsed
                    }
                elif event.type == "content.done":
                    yield {
                        "final_object": event.parsed,
                        "final_json": event.content
                    }
                elif event.type == "refusal.delta":
                    yield {
                        "refusal_delta": event.delta,
                        "refusal_snapshot": event.snapshot
                    }
                elif event.type == "refusal.done":
                    yield {
                        "refusal": event.refusal
                    }

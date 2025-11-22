import os
import json
from typing import Any, AsyncGenerator, Dict, Type
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from ..base import LLMJsonProvider

class AnthropicProvider(LLMJsonProvider):
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=base_url
        )

    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str = "claude-3-5-sonnet-20240620",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams JSON from Anthropic (Claude) using Tool Use (Function Calling) to enforce structure.
        """
        
        tool_name = schema.__name__
        # Convert Pydantic schema to JSON schema
        json_schema = schema.model_json_schema()
        
        tool_definition = {
            "name": tool_name,
            "description": f"Generate a structured {tool_name} object.",
            "input_schema": json_schema
        }
        
        # Force the model to use this tool
        tool_choice = {"type": "tool", "name": tool_name}
        
        messages = [{"role": "user", "content": prompt}]
        
        accumulated_json = ""
        
        async with self.client.messages.stream(
            model=model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=messages,
            tools=[tool_definition],
            tool_choice=tool_choice,
            **kwargs
        ) as stream:
            async for event in stream:
                # For tool use, we look for input_json_delta
                if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                    delta = event.delta.partial_json
                    accumulated_json += delta
                    yield {
                        "delta": delta,
                        "partial_json": accumulated_json
                    }
        
        # Parse final object
        try:
            if accumulated_json:
                final_obj = schema.model_validate_json(accumulated_json)
                yield {
                    "final_object": final_obj,
                    "final_json": accumulated_json
                }
        except Exception:
             yield {"final_json": accumulated_json}

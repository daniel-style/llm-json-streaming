import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, Type
from pydantic import BaseModel
from llm_json_streaming import LLMJsonProvider

class MockProvider(LLMJsonProvider):
    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str = "mock-model",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        # Simulate streaming chunks
        chunks = [
            '{"name": "John"',
            ', "age": 30',
            ', "city": "New York"}'
        ]
        
        accumulated = ""
        for chunk in chunks:
            accumulated += chunk
            yield {
                "delta": chunk,
                "partial_json": accumulated
            }
            await asyncio.sleep(0.01)
            
        # Final object
        yield {"final_object": schema.model_validate_json(accumulated)}

class User(BaseModel):
    name: str
    age: int
    city: str

@pytest.mark.asyncio
async def test_mock_provider_streaming():
    provider = MockProvider()
    prompt = "Get user"
    
    deltas = []
    partials = []
    final_obj = None
    
    async for chunk in provider.stream_json(prompt, User):
        if "delta" in chunk:
            deltas.append(chunk["delta"])
        if "partial_json" in chunk:
            partials.append(chunk["partial_json"])
        if "final_object" in chunk:
            final_obj = chunk["final_object"]
            
    assert "".join(deltas) == '{"name": "John", "age": 30, "city": "New York"}'
    assert partials == [
        '{"name": "John"',
        '{"name": "John", "age": 30',
        '{"name": "John", "age": 30, "city": "New York"}',
    ]
    assert final_obj is not None
    assert final_obj.name == "John"
    assert final_obj.age == 30
    assert final_obj.city == "New York"


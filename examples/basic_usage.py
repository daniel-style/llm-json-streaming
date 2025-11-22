import asyncio
import os
from typing import List
from pydantic import BaseModel
from llm_json_streaming.providers import OpenAIProvider, GeminiProvider, ClaudeProvider

# Define the schema
class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    steps: List[Step]
    final_answer: str

async def run_provider(name, provider, prompt):
    print(f"\n--- Running {name} ---")
    try:
        async for chunk in provider.stream_json(prompt, MathReasoning):
            if "delta" in chunk:
                print(chunk["delta"], end="", flush=True)
            if "final_object" in chunk:
                print(f"\n\n[Parsed Object]: {chunk['final_object']}")
    except Exception as e:
        print(f"\nError running {name}: {e}")

async def main():
    prompt = "Solve this problem: 2x + 5 = 15. Show your reasoning steps."
    
    providers = []
    
    if os.environ.get("OPENAI_API_KEY"):
        providers.append(("OpenAI", OpenAIProvider()))
    
    if os.environ.get("GEMINI_API_KEY"):
        providers.append(("Gemini", GeminiProvider()))
        
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append(("Claude", ClaudeProvider()))
        
    if not providers:
        print("No API keys found. Please set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY.")
        return

    for name, provider in providers:
        await run_provider(name, provider, prompt)

if __name__ == "__main__":
    asyncio.run(main())


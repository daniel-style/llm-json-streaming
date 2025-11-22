import pytest
import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from llm_json_streaming.providers import OpenAIProvider

# Load environment variables from .env file, overriding system envs
load_dotenv(override=True)

class Experience(BaseModel):
    title: str
    company: str
    years: int
    description: str

class Project(BaseModel):
    name: str
    technologies: List[str]
    details: str

class UserInfo(BaseModel):
    name: str
    age: int
    bio: str
    skills: List[str]
    experiences: List[Experience]
    projects: List[Project]

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key", 
                    reason="OPENAI_API_KEY not set")
async def test_openai_integration():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    model = "gpt-4o-mini"
    
    # A more complex prompt to generate longer JSON
    prompt = (
        "Generate a detailed user profile for a senior full-stack engineer. "
        "Include at least 3 work experiences with detailed descriptions, "
        "5 skills, and 2 complex side projects. "
        "Make the bio descriptive and at least 2 sentences long."
    )
    
    print(f"\nPrompt: {prompt}")
    print("-" * 50)
    
    final_object = None
    accumulated_text = ""
    
    async for chunk in provider.stream_json(prompt, UserInfo, model=model):
        if "delta" in chunk:
            delta = chunk["delta"]
            accumulated_text += delta
            print(delta, end="", flush=True)
            
        if "final_object" in chunk:
            final_object = chunk["final_object"]
            
    print("\n" + "-" * 50)
            
    assert final_object is not None
    assert isinstance(final_object, UserInfo)
    assert len(final_object.experiences) >= 3
    assert len(final_object.projects) >= 2
    assert len(final_object.skills) >= 5
    print("\n[Test Passed] Final Object Parsed Successfully:")
    print(f"Name: {final_object.name}")
    print(f"Experiences: {len(final_object.experiences)}")
    print(f"Projects: {len(final_object.projects)}")

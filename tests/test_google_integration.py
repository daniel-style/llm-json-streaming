import pytest
import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from llm_json_streaming.providers import GoogleProvider

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
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY")
    or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key",
    reason="GEMINI_API_KEY not set",
)
async def test_google_integration(capsys):
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GOOGLE_BASE_URL")  # Optional custom base URL

    provider = GoogleProvider(api_key=api_key, base_url=base_url)
    model = "gemini-2.5-flash"

    # A more complex prompt to generate longer JSON
    prompt = (
        "Generate a detailed user profile for a senior full-stack engineer. "
        "Include at least 3 work experiences with detailed descriptions, "
        "5 skills, and 2 complex side projects. "
        "Make the bio descriptive and at least 2 sentences long."
    )

    with capsys.disabled():
        print(f"\nPrompt: {prompt}")
        print("-" * 50)

    final_object = None
    latest_partial_json: Optional[str] = None
    final_json_text: Optional[str] = None

    with capsys.disabled():
        async for chunk in provider.stream_json(prompt, UserInfo, model=model):
            partial_object = chunk.get("partial_object")
            if partial_object is not None:
                print("\033c", end="")  # 清空终端
                print(partial_object, end="", flush=True)
                # 追加到文件方便追踪，每次换行
                with open("partial_object_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"{partial_object}\n")

            partial_json = chunk.get("partial_json")
            if partial_json is not None:
                latest_partial_json = partial_json

            if "final_object" in chunk:
                final_object = chunk["final_object"]
            if "final_json" in chunk:
                final_json_text = chunk["final_json"]

    with capsys.disabled():
        print("\n" + "-" * 50)

    assert final_object is not None
    assert isinstance(final_object, UserInfo)
    assert len(final_object.experiences) >= 3
    assert len(final_object.projects) >= 2
    assert len(final_object.skills) >= 5
    if latest_partial_json and final_json_text:
        assert latest_partial_json.strip() == final_json_text.strip()
    with capsys.disabled():
        print("\n[Test Passed] Final Object Parsed Successfully:")
        print(f"Name: {final_object.name}")
        print(f"Experiences: {len(final_object.experiences)}")
        print(f"Projects: {len(final_object.projects)}")


if __name__ == "__main__":
    asyncio.run(test_google_integration())

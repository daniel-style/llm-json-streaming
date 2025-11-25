#!/usr/bin/env python3
"""
Example demonstrating prefill mode with partial object support using json_repair.
This shows how older Claude models can now provide real-time partial objects during streaming.
"""

import asyncio
import os
from typing import List, Optional
from pydantic import BaseModel
from llm_json_streaming.providers.anthropic_provider import AnthropicProvider


class Task(BaseModel):
    title: str
    description: str
    completed: bool = False


async def main():
    """Demonstrate prefill mode with partial objects."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    provider = AnthropicProvider()

    # Use a model that requires prefill (older Claude model)
    model = "claude-3-haiku-20240307"

    prompt = "Create a task list for a software developer with 3 tasks."

    print(f"Using prefill mode with {model}")
    print("Notice how partial objects are now available in real-time!")
    print("-" * 60)

    task_count = 0
    final_tasks = None

    async for chunk in provider.stream_json(
        prompt=prompt,
        schema=List[Task],
        model=model,
        debug_print=True
    ):
        # Show partial objects when available
        if "partial_object" in chunk:
            partial_tasks = chunk["partial_object"]
            if partial_tasks and len(partial_tasks) > task_count:
                task_count = len(partial_tasks)
                print(f"\n[PARTIAL UPDATE] Now have {task_count} task(s):")
                for i, task in enumerate(partial_tasks):
                    print(f"  {i+1}. {task.title} (completed: {task.completed})")

        # Check for final result
        if "final_object" in chunk:
            final_tasks = chunk["final_object"]
            break

    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    if final_tasks:
        for i, task in enumerate(final_tasks, 1):
            print(f"{i}. {task.title}")
            print(f"   Description: {task.description}")
            print(f"   Completed: {task.completed}\n")
    else:
        print("No final tasks received")


if __name__ == "__main__":
    asyncio.run(main())
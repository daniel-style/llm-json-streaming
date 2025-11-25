import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional, Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from ...base import LLMJsonProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMJsonProvider):
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"), base_url=base_url
        )
        logger.debug("OpenAIProvider initialized (base_url=%s)", base_url or "default")

    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str = "gpt-4o-2024-08-06",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams JSON from OpenAI using Structured Outputs via Chat Completions.
        Uses client.beta.chat.completions.stream which is more compatible with proxies
        than the /v1/responses endpoint, while still supporting Structured Outputs.
        """

        debug_print = self._resolve_debug_print(kwargs.pop("debug_print", None))

        # Use beta.chat.completions.stream for structured outputs
        logger.info("OpenAI streaming start model=%s schema=%s", model, schema.__name__)

        accumulated_json = ""

        async with self.client.beta.chat.completions.stream(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
            temperature=0.0,
            **kwargs,
        ) as stream:
            async for event in stream:
                if event.type == "content.delta":
                    logger.info("OpenAI stream delta chunk received")
                    delta_text = event.delta or ""
                    if event.snapshot is not None:
                        accumulated_json = event.snapshot
                    else:
                        accumulated_json = f"{accumulated_json}{delta_text}"

                    parsed_object = event.parsed or self._safe_parse_json(
                        accumulated_json, schema
                    )
                    looks_like_json = self._looks_like_json_payload(accumulated_json)
                    if parsed_object is None and not looks_like_json:
                        logger.warning(
                            "OpenAI skipping non-JSON chunk (delta preview=%r)",
                            delta_text[:80],
                        )
                        continue

                    if debug_print and delta_text:
                        print(delta_text, end="", flush=True)
                    chunk = {
                        "delta": delta_text,
                        "partial_json": accumulated_json,
                    }
                    if parsed_object is not None:
                        chunk["partial_object"] = parsed_object
                    yield chunk
                elif event.type == "content.done":
                    logger.info("OpenAI stream completed successfully")
                    if debug_print:
                        self._debug_print_separator()
                    yield {"final_object": event.parsed, "final_json": event.content}
                elif event.type == "refusal.delta":
                    logger.warning("OpenAI refusal delta encountered")
                    yield {
                        "refusal_delta": event.delta,
                        "refusal_snapshot": event.snapshot,
                    }
                elif event.type == "refusal.done":
                    logger.warning("OpenAI refusal completed: %s", event.refusal)
                    yield {"refusal": event.refusal}

    def _resolve_debug_print(self, override: Optional[bool]) -> bool:
        if override is not None:
            return override
        env = os.environ.get("LLM_JSON_STREAM_DEBUG_PRINT", "")
        return env.lower() in {"1", "true", "yes", "on"}

    def _debug_print_separator(self) -> None:
        print("\n" + "-" * 50)

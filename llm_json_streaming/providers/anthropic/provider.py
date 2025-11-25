import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional, Type

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from ...base import LLMJsonProvider
from .prefill import PrefillJSONStreamer
from .structured import StructuredOutputStreamer

logger = logging.getLogger(__name__)

STRUCTURED_OUTPUT_BETA = "structured-outputs-2025-11-13"
OFFICIAL_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
STRUCTURED_OUTPUT_MODEL_HINTS = (
    "claude-sonnet-4.5",
    "claude-sonnet-4-5",
    "sonnet-4.5",
    "sonnet-4-5",
    "claude-opus-4.1",
    "claude-opus-4-1",
    "opus-4.1",
    "opus-4-1",
)


class AnthropicProvider(LLMJsonProvider):
    """
    Streams structured JSON from Anthropic (Claude) models.

    Claude Sonnet 4.5 and Claude Opus 4.1 leverage Anthropic's Structured
    Outputs API via `output_format`. All other Claude models avoid tool use
    and instead apply prefilling plus schema-derived instructions.

    Mode selection:
    - "auto": Automatically choose based on model capabilities (default)
    - "structured": Force structured outputs mode
    - "prefill": Force prefill mode
    """

    def __init__(self, api_key: str = None, base_url: str = None, mode: str = "auto"):
        # Validate mode parameter
        valid_modes = {"auto", "structured", "prefill"}
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")

        self._mode = mode
        self._base_url = base_url
        self.client = AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"), base_url=base_url
        )
        logger.debug(
            "AnthropicProvider initialized (mode=%s, base_url=%s)",
            mode,
            base_url or "default",
        )
        self._structured_streamer = StructuredOutputStreamer(
            provider=self,
            structured_output_beta=STRUCTURED_OUTPUT_BETA,
        )
        self._prefill_streamer = PrefillJSONStreamer(provider=self)

    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str = "claude-3-5-sonnet-20240620",
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream JSON from Anthropic. Structured Outputs are used for Claude
        Sonnet 4.5 / Claude Opus 4.1, while other models rely on prefill-based
        JSON streaming (no tool use).

        Args:
            prompt: User prompt used to build the default message list.
            schema: Pydantic model enforced on the response.
            model: Anthropic model identifier.
            use_structured_outputs (bool, optional): Force-enable/disable the
                Structured Outputs pipeline regardless of automatic detection.
        """
        use_structured_outputs = kwargs.pop("use_structured_outputs", None)
        debug_print = self._resolve_debug_print(kwargs.pop("debug_print", None))
        base_is_official = self._is_official_api_base()

        # Determine which mode to use: constructor mode > method parameter > auto-detection
        if self._mode == "structured":
            use_structured_outputs = True
        elif self._mode == "prefill":
            use_structured_outputs = False
        elif use_structured_outputs is not None:
            # Method parameter takes precedence over auto-detection
            use_structured_outputs = bool(use_structured_outputs)
        else:
            # Auto-detection based on model capabilities
            use_structured_outputs = (
                self._supports_structured_outputs(model) and base_is_official
            )

        logger.info(
            "Anthropic streaming start model=%s structured=%s base_official=%s provider_mode=%s",
            model,
            use_structured_outputs,
            base_is_official,
            self._mode,
        )

        print(
            f"[AnthropicProvider stream_json] use_structured_outputs: {use_structured_outputs}"
        )
        if use_structured_outputs:
            async for chunk in self._stream_structured_outputs(
                prompt, schema, model, debug_print=debug_print, **kwargs
            ):
                yield chunk
        else:
            async for chunk in self._stream_prefill_json(
                prompt, schema, model, debug_print=debug_print, **kwargs
            ):
                yield chunk

    async def _stream_structured_outputs(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        *,
        debug_print: bool,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        async for chunk in self._structured_streamer.stream(
            prompt, schema, model, debug_print=debug_print, **kwargs
        ):
            yield chunk

    async def _stream_prefill_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        *,
        debug_print: bool,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        async for chunk in self._prefill_streamer.stream(
            prompt, schema, model, debug_print=debug_print, **kwargs
        ):
            yield chunk

    def _build_schema_instruction(self, schema: Type[BaseModel]) -> str:
        return self._prefill_streamer._build_schema_instruction(schema)

    def _build_prefill_system_prompt(
        self,
        schema: Type[BaseModel],
        *,
        schema_instruction: Optional[str] = None,
    ) -> str:
        return self._prefill_streamer._build_prefill_system_prompt(
            schema, schema_instruction=schema_instruction
        )

    def _build_prefill_stub(self, schema: Type[BaseModel]) -> str:
        return self._prefill_streamer._build_prefill_stub(schema)

    def _detect_prefill_prefix(self, messages: list[dict[str, Any]]) -> str:
        return self._prefill_streamer._detect_prefill_prefix(messages)

    def _merge_prefill_snapshot(self, snapshot: str, prefix: str) -> str:
        return self._prefill_streamer._merge_prefill_snapshot(snapshot, prefix)

    def _supports_structured_outputs(self, model: str) -> bool:
        lowered = (model or "").lower()
        if not lowered:
            return False

        candidate_segments = [lowered]
        if lowered.startswith("claude-"):
            candidate_segments.append(lowered[len("claude-") :])

        for candidate in candidate_segments:
            for hint in STRUCTURED_OUTPUT_MODEL_HINTS:
                if candidate.startswith(hint):
                    return True
        return False

    def _is_official_api_base(self) -> bool:
        """
        Structured Outputs only work against Anthropic's hosted API. If a custom
        proxy/base URL is supplied, we disable the Structured Outputs path.
        """
        if not self._base_url:
            return True

        normalized = self._base_url.rstrip("/").lower()
        return normalized == OFFICIAL_ANTHROPIC_BASE_URL.rstrip("/").lower()

    def _resolve_debug_print(self, override: Optional[bool]) -> bool:
        if override is not None:
            return override
        env = os.environ.get("LLM_JSON_STREAM_DEBUG_PRINT", "")
        return env.lower() in {"1", "true", "yes", "on"}

    def _debug_print_separator(self) -> None:
        print("\n" + "-" * 50)

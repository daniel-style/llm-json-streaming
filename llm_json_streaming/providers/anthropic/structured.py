from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Optional, Type

from pydantic import BaseModel

if TYPE_CHECKING:
    from .provider import AnthropicProvider

logger = logging.getLogger(__name__)


class StructuredOutputStreamer:
    """
    Handles Anthropic's Structured Outputs streaming path.
    """

    def __init__(self, provider: "AnthropicProvider", structured_output_beta: str):
        self._provider = provider
        self._client = provider.client
        self._structured_output_beta = structured_output_beta

    async def stream(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        *,
        debug_print: bool,
        **kwargs: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        max_tokens = kwargs.pop("max_tokens", 4096)
        betas = self._prepare_betas(kwargs.pop("betas", None))
        messages = kwargs.pop("messages", None) or [{"role": "user", "content": prompt}]
        beta_args = {"betas": betas} if betas else {}
        final_emitted = False
        accumulated_text = ""

        logger.debug(
            "Starting structured outputs stream model=%s betas=%s max_tokens=%s",
            model,
            betas,
            max_tokens,
        )

        async with self._client.beta.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            output_format=schema,
            **beta_args,
            **kwargs,
        ) as stream:
            async for event in stream:
                if event.type == "text":
                    delta_text = event.text or ""
                    if event.snapshot is not None:
                        accumulated_text = event.snapshot
                    else:
                        accumulated_text = f"{accumulated_text}{delta_text}"
                    parsed_snapshot: Optional[BaseModel] = None
                    try:
                        parsed_snapshot = event.parsed_snapshot()
                    except Exception:
                        # Partial parses can raise while JSON is still incomplete
                        pass
                    partial_object = parsed_snapshot or self._provider._safe_parse_json(
                        accumulated_text, schema
                    )
                    looks_like_json = self._provider._looks_like_json_payload(
                        accumulated_text
                    )
                    if partial_object is None and not looks_like_json:
                        logger.warning(
                            "Anthropic structured stream skipping non-JSON chunk (delta preview=%r)",
                            delta_text[:80],
                        )
                        continue
                    if debug_print and delta_text:
                        print(delta_text, end="", flush=True)
                    chunk: Dict[str, Any] = {
                        "delta": delta_text,
                        "partial_json": accumulated_text,
                    }
                    if partial_object is not None:
                        chunk["partial_object"] = partial_object
                    yield chunk
                elif event.type == "content_block_stop":
                    payload = self._build_final_payload(event.content_block)
                    if payload:
                        final_emitted = True
                        if debug_print:
                            self._provider._debug_print_separator()
                        yield payload
                elif event.type == "message_stop" and not final_emitted:
                    payload = self._extract_message_payload(event.message)
                    if payload:
                        final_emitted = True
                        if debug_print:
                            self._provider._debug_print_separator()
                        yield payload

    def _prepare_betas(self, incoming_betas: Any) -> List[str]:
        if incoming_betas is None:
            betas: List[str] = []
        elif isinstance(incoming_betas, str):
            betas = [incoming_betas]
        else:
            betas = list(incoming_betas)

        if self._structured_output_beta not in betas:
            betas.append(self._structured_output_beta)
        return betas

    def _build_final_payload(self, content_block: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        final_obj = getattr(content_block, "parsed_output", None)
        final_json = getattr(content_block, "text", None)

        if final_obj is not None:
            payload["final_object"] = final_obj
        if final_json is not None:
            payload["final_json"] = final_json
        return payload

    def _extract_message_payload(self, message: Any) -> Dict[str, Any]:
        for block in getattr(message, "content", []):
            payload = self._build_final_payload(block)
            if payload:
                return payload
        return {}

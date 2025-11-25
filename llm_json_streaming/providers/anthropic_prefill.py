from __future__ import annotations

import json
import logging
import textwrap
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Optional, Type

from pydantic import BaseModel

from json_repair import repair_json

if TYPE_CHECKING:
    from .anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class PrefillJSONStreamer:
    """
    Handles Anthropic's prefill-based JSON streaming path.
    """

    def __init__(self, provider: "AnthropicProvider"):
        self._provider = provider
        self._client = provider.client

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
        messages = kwargs.pop("messages", None)
        prefill_prefix = ""

        schema_instruction: Optional[str] = None
        if messages is None:
            schema_instruction = self._build_schema_instruction(schema)
            prefixed_prompt = prompt.strip()
            prefill = self._build_prefill_stub(schema)
            messages = [
                {"role": "user", "content": prefixed_prompt},
                {"role": "assistant", "content": prefill},
            ]
            prefill_prefix = prefill
        else:
            prefill_prefix = self._detect_prefill_prefix(messages)

        accumulated_text = prefill_prefix
        logger.debug(
            "Starting prefill stream model=%s max_tokens=%s has_custom_messages=%s",
            model,
            max_tokens,
            messages is not None,
        )

        incoming_system_prompt = kwargs.pop("system", None)
        schema_instruction = schema_instruction or self._build_schema_instruction(
            schema
        )
        if incoming_system_prompt:
            system_prompt = (
                f"{incoming_system_prompt.strip()}\n\n{schema_instruction}".strip()
            )
        else:
            system_prompt = self._build_prefill_system_prompt(
                schema, schema_instruction=schema_instruction
            )

        print(f"[AnthropicProvider prefill] system_prompt:\n{system_prompt}\n")
        async with self._client.beta.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system_prompt,
            **kwargs,
        ) as stream:
            async for event in stream:
                if event.type == "text":
                    snapshot = event.snapshot or ""
                    accumulated_text = self._merge_prefill_snapshot(
                        snapshot, prefill_prefix
                    )
                    delta_text = event.text or ""

                    # Try direct parsing first
                    partial_object = self._provider._safe_parse_json(
                        accumulated_text, schema
                    )

                    # If direct parsing fails, try json_repair for partial completion
                    if partial_object is None:
                        partial_object = self._try_repair_and_parse(
                            accumulated_text, schema
                        )

                    looks_like_json = self._provider._looks_like_json_payload(
                        accumulated_text
                    )
                    if partial_object is None and not looks_like_json:
                        logger.warning(
                            "Anthropic prefill stream skipping non-JSON chunk (delta preview=%r)",
                            delta_text[:80],
                        )
                        continue
                    if debug_print and delta_text:
                        print(delta_text, end="", flush=True)
                    chunk = {
                        "delta": delta_text,
                        "partial_json": accumulated_text,
                    }
                    if partial_object is not None:
                        chunk["partial_object"] = self._normalize_partial_object(partial_object)
                    yield chunk
                elif event.type == "message_stop":
                    payload = self._parse_text_message(
                        event.message, schema, accumulated_text, prefill_prefix
                    )
                    if payload:
                        logger.debug(
                            "Prefill stream produced final payload keys=%s",
                            list(payload.keys()),
                        )
                        if debug_print:
                            self._provider._debug_print_separator()
                        yield payload

    def _build_schema_instruction(self, schema: Type[BaseModel]) -> str:
        json_schema = schema.model_json_schema()
        schema_example = self._build_schema_example(schema)
        summary_lines = self._summarize_schema_fields(json_schema)
        summary_block = (
            "\n".join(summary_lines)
            if summary_lines
            else "• Follow the schema exactly."
        )
        required_fields = ", ".join(json_schema.get("required") or []) or "none"

        instructions = f"""
        ### JSON generation rules
        1. Respond with a SINGLE JSON object. No prose, no markdown, no explanations.
        2. The first character you emit must be '{{' and the last must be '}}'. Do not emit backticks.
        3. Populate every required field ({required_fields}). Optional fields may be omitted but must still satisfy the schema if included.
        4. Strings MUST be double quoted. Do not invent fields that are not in the schema.
        5. Stop immediately after finishing the JSON object—never append commentary.

        ### Field requirements
        {summary_block}

        ### Example JSON (replicate this structure exactly)
        {schema_example}
        """
        return textwrap.dedent(instructions).strip()

    def _build_prefill_stub(self, schema: Type[BaseModel]) -> str:
        """
        Prefill with an opening brace or optionally include the first key to
        help Claude skip generic preambles. No trailing whitespace allowed.
        """
        json_schema = schema.model_json_schema()
        properties = list((json_schema.get("properties") or {}).keys())
        if properties:
            first_key = properties[0]
            return f'{{\n  "{first_key}":'
        return "{"

    def _build_prefill_system_prompt(
        self,
        schema: Type[BaseModel],
        *,
        schema_instruction: Optional[str] = None,
    ) -> str:
        json_schema = schema.model_json_schema()
        required_fields = ", ".join(json_schema.get("required") or []) or "none"
        instructions = f"""
        You are a strict JSON generator. You MUST produce EXACTLY one valid JSON object that matches the provided schema—no text or formatting outside the JSON is permitted.

        Rules:
        • You MUST respond with a single JSON object and nothing else.
        • Begin your reply with '{{' and end with '}}'.
        • Fill every required field ({required_fields}) and keep types exact.
        • Never emit prose, markdown, code fences, or commentary.
        • If unsure, output the closest valid JSON you can, but still obey the schema.
        • Once the JSON object is complete, stop responding immediately.
        """
        instructions = textwrap.dedent(instructions).strip()
        if schema_instruction:
            instructions = f"{instructions}\n\n{schema_instruction}".strip()
        return instructions

    def _summarize_schema_fields(self, json_schema: Dict[str, Any]) -> List[str]:
        properties = json_schema.get("properties") or {}
        required_fields = set(json_schema.get("required") or [])
        summaries: List[str] = []

        for name, details in properties.items():
            if not isinstance(details, dict):
                continue
            field_type = self._describe_schema_type(details)
            requirement = "required" if name in required_fields else "optional"
            constraints = self._collect_field_constraints(details)
            desc = details.get("description")

            parts = [f'• "{name}" ({field_type}, {requirement})']
            if constraints:
                parts.append(f"[{'; '.join(constraints)}]")
            if desc:
                parts.append(f"- {desc.strip()}")

            summaries.append(" ".join(parts))

        return summaries

    def _describe_schema_type(self, node: Dict[str, Any]) -> str:
        node_type = node.get("type")
        if isinstance(node_type, list):
            node_type = "/".join(node_type)
        if node_type:
            if node_type == "array":
                items = node.get("items") or {}
                item_type = (
                    self._describe_schema_type(items)
                    if isinstance(items, dict)
                    else "any"
                )
                return f"array<{item_type}>"
            if node_type == "object":
                props = node.get("properties") or {}
                return f"object<{', '.join(props.keys()) or '...'}>"
            return str(node_type)
        if "$ref" in node:
            return str(node["$ref"])
        return "any"

    def _collect_field_constraints(self, node: Dict[str, Any]) -> List[str]:
        constraints: List[str] = []
        for key in (
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "minItems",
            "maxItems",
        ):
            if key in node:
                constraints.append(f"{key}={node[key]}")
        if node.get("enum"):
            constraints.append(f"enum={node['enum']}")
        if node.get("format"):
            constraints.append(f"format={node['format']}")
        return constraints

    def _build_schema_example(self, schema: Type[BaseModel]) -> str:
        json_schema = schema.model_json_schema()
        example_obj = self._build_example_from_schema(json_schema, json_schema) or {}
        return json.dumps(example_obj, indent=2, ensure_ascii=False)

    def _build_example_from_schema(
        self,
        node: Dict[str, Any],
        root_schema: Dict[str, Any],
    ) -> Any:
        if not isinstance(node, dict):
            return None

        if "enum" in node and node["enum"]:
            return node["enum"][0]

        ref = node.get("$ref")
        if ref:
            ref_name = ref.split("/")[-1]
            defs = root_schema.get("$defs") or root_schema.get("definitions") or {}
            target = defs.get(ref_name, {})
            return self._build_example_from_schema(target, root_schema)

        node_type = node.get("type")
        if isinstance(node_type, list):
            node_type = node_type[0]

        if node_type == "object":
            props = node.get("properties") or {}
            example: Dict[str, Any] = {}
            for name, child in props.items():
                value = self._build_example_from_schema(child, root_schema)
                if value is None:
                    value = self._default_scalar_example(child)
                example[name] = value
            return example

        if node_type == "array":
            items = node.get("items") or {}
            item_example = self._build_example_from_schema(items, root_schema)
            if item_example is None:
                item_example = self._default_scalar_example(items)
            return [item_example]

        return (
            node.get("default")
            or (node.get("examples") or [None])[0]
            or self._default_scalar_example(node)
        )

    def _default_scalar_example(self, node: Dict[str, Any]) -> Any:
        node_type = node.get("type")
        if isinstance(node_type, list):
            node_type = node_type[0]

        if node_type == "string":
            fmt = node.get("format")
            if fmt == "date":
                return "2024-01-01"
            if fmt == "date-time":
                return "2024-01-01T00:00:00Z"
            return "string"
        if node_type == "integer":
            return 0
        if node_type == "number":
            return 0.0
        if node_type == "boolean":
            return True
        if node_type == "array":
            return []
        if node_type == "object":
            return {}
        return None

    def _detect_prefill_prefix(self, messages: List[Dict[str, Any]]) -> str:
        if not messages:
            return ""
        last = messages[-1]
        if last.get("role") != "assistant":
            return ""
        content = last.get("content")
        if isinstance(content, str):
            return content
        return ""

    def _merge_prefill_snapshot(self, snapshot: str, prefix: str) -> str:
        if not prefix:
            return snapshot
        if not snapshot:
            return prefix
        if snapshot.startswith(prefix):
            return snapshot
        return f"{prefix}{snapshot}"

    def _normalize_partial_object(self, obj: Any) -> Any:
        """
        Ensure partial_object payloads are serialized as dictionaries so they match
        the structured-output format and print as JSON when logged.
        """
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return obj

    def _try_repair_and_parse(
        self, json_text: str, schema: Type[BaseModel]
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to repair incomplete JSON using json_repair and parse it into a dictionary.
        This enables partial object support for prefill mode without enforcing schema validation.
        """
        if not json_text:
            return None

        # Only attempt repair if the text looks like JSON but is incomplete
        if not self._provider._looks_like_json_payload(json_text):
            return None

        try:
            # Use json_repair to fix and complete the JSON
            repaired_json = repair_json(json_text, ensure_ascii=False)

            # Parse the repaired JSON into a python object without schema validation.
            parsed_data = json.loads(repaired_json)
            if not isinstance(parsed_data, dict):
                logger.debug(
                    "Repaired JSON is not an object; skipping partial object construction."
                )
                return None
            logger.debug(
                "Successfully repaired and parsed partial JSON (original_len=%d, repaired_len=%d)",
                len(json_text),
                len(repaired_json),
            )
            return parsed_data
        except Exception as e:
            # If repair still fails, return None and let the caller handle it
            logger.debug(
                "JSON repair failed for partial parsing: %s (text_preview=%r)",
                str(e),
                json_text[:100] if json_text else "",
            )
            return None

    def _parse_text_message(
        self,
        message: Any,
        schema: Type[BaseModel],
        accumulated_text: str,
        prefill_prefix: str = "",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        candidate_text: Optional[str] = None

        for block in getattr(message, "content", []):
            if getattr(block, "type", None) == "text":
                candidate_text = getattr(block, "text", "")
                break

        candidate_text = candidate_text or accumulated_text
        candidate_text = self._merge_prefill_snapshot(
            candidate_text or "", prefill_prefix
        )

        # Try direct parsing first
        final_obj = self._provider._safe_parse_json(candidate_text, schema)

        # If direct parsing fails, try json_repair for final completion
        if final_obj is None:
            final_obj = self._try_repair_and_parse(candidate_text, schema)

        if final_obj is not None:
            payload["final_object"] = final_obj
            payload["final_json"] = candidate_text
            logger.debug(
                "Successfully parsed final JSON for schema=%s", schema.__name__
            )
        elif candidate_text:
            payload["final_json"] = candidate_text
            logger.warning(
                "Failed to parse final JSON for schema=%s; returning raw text",
                schema.__name__,
            )

        return payload

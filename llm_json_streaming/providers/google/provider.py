import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional, Type

from google import genai
from google.genai import types
from json_repair import repair_json
from pydantic import BaseModel

from ...base import LLMJsonProvider

logger = logging.getLogger(__name__)


class GoogleProvider(LLMJsonProvider):
    """Google Gemini provider for JSON streaming using structured outputs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gemini-2.5-flash",
        **kwargs,
    ):
        """
        Initialize Google provider.

        Args:
            api_key: Google API key. If not provided, uses GOOGLE_API_KEY env var.
            base_url: Optional custom base URL.
            default_model: Default Gemini model to use.
            **kwargs: Additional arguments for the Google client.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )

        self.default_model = default_model

        # Initialize Google GenAI client
        client_config = {}
        if base_url:
            client_config["base_url"] = base_url

        self.client = genai.Client(api_key=self.api_key, **client_config)

    def _looks_like_json_payload(self, text: str) -> bool:
        """Check if text looks like it contains JSON content."""
        text = text.strip()
        return text.startswith("{") or text.startswith("[")

    def _try_repair_json(self, json_text: str) -> Optional[str]:
        """
        Attempt to repair incomplete JSON using json_repair and return the repaired JSON string.
        This allows the repaired JSON to be parsed with schema validation like structured outputs.
        """
        if not json_text:
            return None

        # Only attempt repair if the text looks like JSON but is incomplete
        if not self._looks_like_json_payload(json_text):
            return None

        try:
            # Use json_repair to fix and complete the JSON
            repaired_json = repair_json(json_text, ensure_ascii=False)
            logger.debug(
                f"Successfully repaired incomplete JSON: {len(json_text)} -> {len(repaired_json)} chars"
            )
            return repaired_json
        except Exception as e:
            logger.warning(f"JSON repair failed: {e}")
            return None

    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream JSON response from Google Gemini using structured outputs.

        Args:
            prompt: The input prompt for the model.
            schema: Pydantic model class for response validation.
            model: Gemini model to use. Defaults to provider's default_model.
            **kwargs: Additional generation parameters.

        Yields:
            Dictionaries containing streaming response data with keys:
            - partial_object: Best effort parsed partial object
            - delta: Raw text chunk
            - partial_json: Accumulated JSON text
            - final_object: Complete validated object when finished
            - final_json: Complete JSON text when finished
        """
        model_name = model or self.default_model

        # Configure generation with structured output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
            **kwargs,
        )

        accumulated_json = ""

        try:
            # Generate streaming content
            response_stream = self.client.models.generate_content_stream(
                model=model_name, contents=prompt, config=config
            )

            for chunk in response_stream:
                if (
                    chunk.candidates
                    and chunk.candidates[0].content
                    and chunk.candidates[0].content.parts
                ):
                    text_chunk = chunk.candidates[0].content.parts[0].text
                    if text_chunk:
                        # According to Google docs, streamed chunks will be valid partial JSON strings
                        # that can be concatenated to form the final complete JSON object
                        accumulated_json += text_chunk

                        partial_object = self._safe_parse_json(accumulated_json, schema)

                        if partial_object is None:
                            repaired_json = self._try_repair_json(accumulated_json)
                            if repaired_json is not None:
                                partial_object = self._safe_parse_json(
                                    repaired_json, schema
                                )

                        if partial_object is None:
                            partial_object = self._try_repair_and_parse(
                                accumulated_json
                            )

                        looks_like_json = self._looks_like_json_payload(
                            accumulated_json
                        )
                        if partial_object is None and not looks_like_json:
                            logger.warning(
                                "Google stream skipping non-JSON chunk (preview=%r)",
                                text_chunk[:80],
                            )
                            continue

                        chunk_payload: Dict[str, Any] = {
                            "delta": text_chunk,
                            "partial_json": accumulated_json,
                        }
                        if partial_object is not None:
                            chunk_payload["partial_object"] = (
                                self._normalize_partial_object(partial_object)
                            )
                        yield chunk_payload

            # Final validation and yield
            try:
                final_object = schema.model_validate_json(accumulated_json)
                yield {"final_object": final_object, "final_json": accumulated_json}
            except Exception as e:
                logger.warning(f"Failed to validate final JSON: {e}")
                # Still yield the raw JSON
                yield {"final_json": accumulated_json}

        except Exception as e:
            logger.error(f"Error in Google provider streaming: {e}")
            raise

    def _try_repair_and_parse(self, json_text: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to repair incomplete JSON using json_repair and parse it into a dictionary.
        """
        if not json_text:
            return None

        if not self._looks_like_json_payload(json_text):
            return None

        try:
            repaired_json = repair_json(json_text, ensure_ascii=False)
            parsed_data = json.loads(repaired_json)
            if not isinstance(parsed_data, dict):
                logger.debug(
                    "Repaired JSON is not an object; skipping partial object construction."
                )
                return None
            return parsed_data
        except Exception as e:
            logger.debug(
                "JSON repair failed for partial parsing: %s (preview=%r)",
                str(e),
                json_text[:100] if json_text else "",
            )
            return None

    def _normalize_partial_object(self, obj: Any) -> Any:
        """Ensure partial_object payloads are serialized as dictionaries for logging/compat."""
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return obj

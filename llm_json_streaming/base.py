from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, Type, Union
from pydantic import BaseModel
try:
    from json_repair import repair_json
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False

class LLMJsonProvider(ABC):
    """
    Abstract base class for LLM providers that support streaming JSON.
    """

    @abstractmethod
    async def stream_json(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream JSON updates from the LLM.
        
        Args:
            prompt: The input prompt.
            schema: The Pydantic model class defining the expected structure.
            model: The specific model version to use.
            **kwargs: Additional provider-specific arguments.

        Yields:
            Dict[str, Any]: Partial or complete JSON chunks as dictionaries. 
                            (Note: Exact behavior depends on implementation, ideally yields accumulated valid state or delta)
        """
        pass

    def _safe_parse_json(
        self,
        json_text: str,
        schema: Type[BaseModel],
        repair_partial: bool = True,
    ) -> Optional[BaseModel]:
        """
        Attempt to parse JSON text against the provided schema.
        Returns None when the text is empty, incomplete, or invalid.

        Args:
            json_text: The JSON text to parse.
            schema: The Pydantic model class defining the expected structure.
            repair_partial: Whether to attempt repairing partial JSON using json-repair.
        """
        if not json_text:
            return None
        stripped = json_text.strip()
        if not stripped:
            return None

        # First try direct parsing
        try:
            return schema.model_validate_json(stripped)
        except Exception:
            pass

        # If direct parsing fails and json-repair is available, try repairing
        if repair_partial and JSON_REPAIR_AVAILABLE and self._looks_like_json_payload(stripped):
            try:
                repaired_json = repair_json(stripped, ensure_ascii=False)
                return schema.model_validate_json(repaired_json)
            except Exception:
                pass

        return None

    def _get_best_partial_json(
        self,
        json_text: str,
        schema: Type[BaseModel],
    ) -> tuple[Optional[BaseModel], Optional[str]]:
        """
        Get the best possible partial/complete JSON parsing result.

        Returns a tuple of (parsed_object, repaired_json_text).
        - parsed_object: The Pydantic model instance if parsing succeeds, None otherwise
        - repaired_json_text: The repaired JSON text if repair was attempted, original text otherwise

        Args:
            json_text: The JSON text to parse.
            schema: The Pydantic model class defining the expected structure.
        """
        if not json_text:
            return None, None

        stripped = json_text.strip()
        if not stripped:
            return None, None

        # First try direct parsing
        try:
            parsed_object = schema.model_validate_json(stripped)
            return parsed_object, stripped
        except Exception:
            pass

        # If direct parsing fails and json-repair is available, try repairing
        if JSON_REPAIR_AVAILABLE and self._looks_like_json_payload(stripped):
            try:
                repaired_json = repair_json(stripped, ensure_ascii=False)
                parsed_object = schema.model_validate_json(repaired_json)
                return parsed_object, repaired_json
            except Exception:
                pass

        return None, stripped

    def _looks_like_json_payload(self, json_text: str) -> bool:
        """
        Lightweight heuristic to decide whether a string could be JSON.
        Helps filter out obvious non-JSON responses (e.g., prose).
        """
        if not json_text:
            return False
        stripped = json_text.lstrip()
        if not stripped:
            return False
        return stripped[0] in {"{", "["}


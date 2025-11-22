from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, Type, Union
from pydantic import BaseModel

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


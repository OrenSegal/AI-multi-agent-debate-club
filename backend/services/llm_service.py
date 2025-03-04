import logging
from typing import List, Dict, Any, Optional

import openrouter
from langchain.llms.base import LLM
from langchain.schema import LLMResult
from config import OPENROUTER_MODEL
import os

logger = logging.getLogger(__name__)


class OpenRouterLLM(LLM):
    """LLM wrapper for OpenRouter API."""
    
    model_name: str = OPENROUTER_MODEL
    temperature: float = 0.7
    max_tokens: int = 1024
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Initialize OpenRouter LLM."""
        super().__init__(**kwargs)
        
        if model_name:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
            
        # Set up OpenRouter client
        openrouter.api_key = os.getenv("OPENROUTER_API_KEY")
        
        logger.info(f"Initialized OpenRouter LLM with model: {self.model_name}")
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call the OpenRouter API with a prompt and return the response."""
        try:
            response = openrouter.Completion.create(
                model=self.model_name,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=stop
            )
            
            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            raise
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "openrouter"


# Singleton instance for reuse
_llm_instance = None

def get_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> OpenRouterLLM:
    """Get a singleton instance of the OpenRouter LLM."""
    global _llm_instance
    
    if _llm_instance is None or model_name or temperature is not None or max_tokens is not None:
        _llm_instance = OpenRouterLLM(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    return _llm_instance
import httpx
import time
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logger = logging.getLogger(__name__)

class LLMAPIClient:
    """Client for interacting with LLM APIs with retry capability."""
    
    def __init__(self, api_url: str, api_key: str, timeout: float = 60.0):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def generate_arguments(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate arguments using the LLM API with retry capability."""
        logger.info(f"Sending request to LLM API: {prompt[:50]}...")
        
        try:
            logger.debug(f"Making HTTP POST request to LLM API at {time.strftime('%H:%M:%S')}")
            
            response = await self.client.post(
                self.api_url,
                json={"prompt": prompt, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            logger.info(f"Received response from LLM API: Status {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Error response from LLM API: {response.text}")
                raise Exception(f"LLM API returned status code {response.status_code}: {response.text}")
            
            response_data = response.json()
            logger.debug("Successfully parsed response JSON")
            return response_data["text"]
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_arguments: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

from backend.config import get_llm_config

# Create a singleton instance
config = get_llm_config()
llm_api_client = LLMAPIClient(
    api_url=config.api_url,
    api_key=config.api_key,
    timeout=config.timeout
)
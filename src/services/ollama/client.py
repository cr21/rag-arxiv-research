import logging
from typing import Dict
import httpx
from src.config import Settings
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama client for interacting with the Ollama API.

    """

    def __init__(self, settings: Settings):
        self.ollama_host = settings.ollama_host
        self.ollama_timeout = settings.ollama_timeout

    async def health_check(self)-> Dict[str, str]:
        """
        Check if Ollama service is running or not
        """

        try:
            async with httpx.AsyncClient(base_url=self.ollama_host, timeout=self.ollama_timeout) as client:
                response = await client.get(f"/api/tags")  # Just the path without the base URL because base_url is already set in the client.
                if response.status_code == 200:
                    return {'status':'ok', 'message':'ollama service is running'}
                else:
                    return {'status':'unhealthy', 'message':f'ollama service is not running with status code {response.status_code}'}
        except Exception as e:
            logger.error(f"Error checking Ollama health: {e}")
            return {'status':'unhealthy', 'message':f'Error checking Ollama health: {e}'}
        
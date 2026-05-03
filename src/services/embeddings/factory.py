from typing import Optional

from src.config import Settings, get_settings
from .openai_client import OpenAIEmbeddingsClient


def make_embeddings_service(settings: Optional[Settings] = None) -> OpenAIEmbeddingsClient:
    """Factory function to create embeddings service."""
    if settings is None:
        settings = get_settings()
    return OpenAIEmbeddingsClient(api_key=settings.openai_api_key)


def make_embeddings_client(settings: Optional[Settings] = None) -> OpenAIEmbeddingsClient:
    """Factory function to create embeddings client."""
    if settings is None:
        settings = get_settings()
    return OpenAIEmbeddingsClient(api_key=settings.openai_api_key)
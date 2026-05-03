from typing import List, Dict
from pydantic import BaseModel


class OpenAIEmbeddingRequest(BaseModel):
    """Request model for OpenAI embeddings API."""
    model: str = "text-embedding-3-small"
    input: List[str]
    dimensions: int = 1536


class OpenAIEmbeddingResponse(BaseModel):
    """Response model from OpenAI embeddings API."""
    model: str
    object: str = "list"
    usage: Dict[str, int]
    data: List[Dict]

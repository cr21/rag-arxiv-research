import logging
from typing import List
import httpx
from src.schemas.embeddings.openai import OpenAIEmbeddingRequest, OpenAIEmbeddingResponse

logger = logging.getLogger(__name__)


class OpenAIEmbeddingsClient:
    """Client for OpenAI embeddings API using text-embedding-3-small (1536 dimensions)."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"OpenAI Embeddings Client initialized with base URL: {self.base_url}")

    async def embed_documents(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Embed text passages for indexing."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            request_data = OpenAIEmbeddingRequest(
                model="text-embedding-3-small",
                input=batch,
                dimensions=1536,
            )

            try:
                response = await self.client.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json=request_data.model_dump(),
                )
                response.raise_for_status()
                result = OpenAIEmbeddingResponse(**response.json())
                batch_embeddings = [item["embedding"] for item in result.data]
                embeddings.extend(batch_embeddings)
                logger.debug(f"Embedded batch of {len(batch)} passages")

            except httpx.HTTPError as e:
                logger.error(f"Error embedding passages: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in embed_documents: {e}")
                raise

        logger.info(f"Successfully embedded {len(embeddings)} passages")
        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Embed a search query."""
        request_data = OpenAIEmbeddingRequest(
            model="text-embedding-3-small",
            input=[query],
            dimensions=1536,
        )

        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json=request_data.model_dump(),
            )
            response.raise_for_status()
            result = OpenAIEmbeddingResponse(**response.json())
            embedding = result.data[0]["embedding"]
            logger.debug(f"Embedded query: '{query[:50]}...'")
            return embedding

        except httpx.HTTPError as e:
            logger.error(f"Error embedding query: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed_query: {e}")
            raise

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

from errno import EMSGSIZE
import logging
from typing import List
import httpx
from src.schemas.embeddings.jina import JinaEmbeddingRequest, JinaEmbeddingResponse

logger = logging.getLogger(__name__)

class JinaEmbeddingsClient:
    """
    Client for Jina AI embeddings API.

    Uses Jina embeddings v3 model with 1024 dimensions optimized for retrieval.
    Documentation: https://jina.ai/embeddings
    """
    def __init__(self, api_key:str, base_url:str='https://api.jina.ai/v1'):
        """
        Initialize Jina Embeddings Client.

        :param api_key: Jina AI API key
        :param base_url: Base URL for Jina AI API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"Jina Embeddings Client initialized with base URL: {self.base_url}")
    
    async def embed_documents(self, texts:List[str], batch_size:int=10) -> List[List[float]]:
        """
        Embed text passages for indexing.
        :param texts: List of text passages to embed
        :param batch_size: Number of passages to embed in each batch
        :returns: List of embeddings
        """
        embeddings=[]

        for i in range(0, len(texts), batch_size):
            batch =texts[i:i+batch_size]
            request_data = JinaEmbeddingRequest(model='jina-embeddings-v3', 
                task='retrieval.passage', 
                dimensions=1024, input=batch)

            try:
                response = await self.client.post(
                    f"{self.base_url}/embeddings", headers=self.headers, json=request_data.model_dump()
                )
                response.raise_for_status()
                result = JinaEmbeddingResponse.model_validate_json(response.json())
                batch_embeddings = [embedding['embedding'] for embedding in result.data]
                embeddings.extend(batch_embeddings)
                logger.debug(f"Embedded batch of {len(batch)} passages" )

            except httpx.HTTPError as e:
                logger.error(f"Error embedding passages: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in embed_passages: {e}")
                raise
        logger.info(f"Successfully embedded {len(embeddings)} passages")
        return embeddings


    async def embed_query(self, query: str) -> List[float]:
        """Embed a search query.

        :param query: Query text to embed
        :returns: Embedding vector for the query
        """
        request_data = JinaEmbeddingRequest(model="jina-embeddings-v3", task="retrieval.query", dimensions=1024, input=[query])

        try:
            response = await self.client.post(f"{self.base_url}/embeddings", headers=self.headers, json=request_data.model_dump())
            response.raise_for_status()

            result = JinaEmbeddingResponse(**response.json())
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
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()




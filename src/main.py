import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.config import get_settings
from src.db.factory import make_database
from src.routers import ping, papers, ask, search
# from src.routers import ask, paper, ping
from src.services.arxiv.factory import make_arxiv_client
from src.services.pdf_parser.factory import make_pdf_parser_service
from src.services.opensearch.factory import make_opensearch_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    """
    logger.info("Starting up...")
    settings = get_settings()
    app.state.settings = settings
    logger.info(f"Settings loaded: {settings.model_dump_json(indent=2)}")

    database = make_database()
    app.state.database = database
    logger.info("Database initialized")
    # opensearch service
    opensearch_client = make_opensearch_client()
    app.state.opensearch_client = opensearch_client
    # verify opensearch connnectivty and create index if needed
    if opensearch_client.health_check():
        logger.info("Opensearch health check passed")
        # Ensure index exists
        if opensearch_client.create_index(force=False):
            logger.info("Opensearch index created")
        else:
            logger.error("Opensearch index already exists")
        # GEt stats of the index
        stats = opensearch_client.get_index_stats()
        logger.info(f"OpenSearch ready: {stats.get('document_count', 0)} documents indexed")
    else:
        logger.warning("OpenSearch connection failed - search features will be limited")


    app.state.arxiv_client = make_arxiv_client()
    app.state.llm_service = None
    app.state.pdf_parser = make_pdf_parser_service()
    logger.info("Services initialized: arXiv API client, PDF parser, OpenSearch client")
    logger.info("API READY")
    yield
    logger.info("Shutting down... Cleaning up resources")
    database.teardown()
    logger.info("API SHUTDOWN")


app = FastAPI(lifespan=lifespan,
    title="RAG on arxiv research paper",
    description="RAG on arxiv research paper",
    version=os.getenv("APP_VERSION", "0.1.0"),
    # root_path="/api/v1",
    contact={
        "name": "Chirag Tagadiya",
        "email": "cr.tagadiya@gmail.com",
    }
)


# ADD ROUTERS
app.include_router(ping.router, prefix="/api/v1")
app.include_router(papers.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


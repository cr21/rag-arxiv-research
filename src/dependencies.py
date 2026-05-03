from functools import lru_cache
from typing import Annotated, Generator, Any
from fastapi import Depends, Request

# remove apikey authentication for now 
from sqlalchemy.orm import Session
from src.config import Settings
from src.db.interface.base import IBaseDatabase
from src.services.opensearch.client import OpenSearchClient
from src.services.embeddings.openai_client import OpenAIEmbeddingsClient
from src.services.pdf_parser.parser import PDFParserService
from src.services.arxiv.client import ArxivClient

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get settings.
    """
    return Settings()

def get_request_settings(request: Request)-> Settings:
    """
    Get settings from the request.
    """
    return request.app.state.settings

def get_database(request: Request)-> IBaseDatabase:
    """ 
    Get database instance from the request.
    """
    return request.app.state.database


def get_db_session(database: Annotated[IBaseDatabase, Depends(get_database)])-> Generator[Session, None, None]:
    """
    Get a new database session.
    """
    with database.get_session() as session:
        yield session

   
def get_pdf_parser_service(request: Request):
    """
    Get PDF parser service instance from the request.
    """
    return None

def get_llm_service(request: Request):
    """
    Get LLM service instance from the request.
    """
    return None

def get_opensearch_client(request: Request):
    """
    Get Opensearch service instance from the request.
    """
    return request.app.state.opensearch_client

def get_arxiv_client(request: Request) -> ArxivClient:
    """Get arXiv client from the request state."""
    return request.app.state.arxiv_client


def get_pdf_parser(request: Request) -> PDFParserService:
    """Get PDF parser service from the request state."""
    return request.app.state.pdf_parser


def get_embeddings_service(request: Request) -> OpenAIEmbeddingsClient:
    """Get embeddings service from the request state."""
    return request.app.state.embeddings_service

# depedency type aliases
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[IBaseDatabase, Depends(get_database)]
SessionDep = Annotated[Session, Depends(get_db_session)]
ArxivDep = Annotated[ArxivClient, Depends(get_arxiv_client)]
PDFParserDep = Annotated[PDFParserService, Depends(get_pdf_parser)]
LLMServiceDep = Annotated[Any, Depends(get_llm_service)]
OpenSearchDep = Annotated[OpenSearchClient, Depends(get_opensearch_client)]
EmbeddingsDep = Annotated[OpenAIEmbeddingsClient, Depends(get_embeddings_service)]
from functools import lru_cache
from typing import Annotated, Generator, Any
from fastapi import Depends, Request

# remove apikey authentication for now 
from sqlalchemy.orm import Session
from src.config import Settings
from src.db.interface.base import IBaseDatabase

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

def get_opensearch_service(request: Request):
    """
    Get Opensearch service instance from the request.
    """
    return None

# depedency type aliases
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[IBaseDatabase, Depends(get_database)]
SessionDep = Annotated[Session, Depends(get_db_session)]
PdfParserServiceDep = Annotated[Any, Depends(get_pdf_parser_service)]
LLMServiceDep = Annotated[Any, Depends(get_llm_service)]
OpensearchServiceDep = Annotated[Any, Depends(get_opensearch_service)]

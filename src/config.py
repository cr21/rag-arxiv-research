from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DefaultSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",
        extra="ignore",
        frozen=True,
        env_nested_delimiter="__",
    )
    

class ArxivSettings(BaseSettings):
    """
    Arxive API Client Settings
    """
    base_url: str = "https://export.arxiv.org/api/query"
    namespace: dict = Field(default={
        "atom": "http://www.w3.org/2005/Atom",
        "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        "arxiv": "http://arxiv.org/schemas/atom"
    })
    pdf_cache_dir: str = "./data/arxiv_pdfs"
    rate_limit_delay: float = 3.0
    timeout_seconds: int = 30
    max_results: int = 100
    search_category: str = "cs.AI"

class PDFParserSettings(BaseSettings):
    """
    PDF Parser Settings
    """
    max_pages: int = 20
    max_file_size_mb: int = 20
    do_ocr: bool = False
    do_table_structure: bool = True

class Settings(DefaultSettings):
    """
    Application settings.
    """
    app_version: str  = "0.1.0"
    debug: bool = True
    environment: str = "development"
    service_name: str = "rag-api"


    # POSTGRES CONFIG
    postgres_database_url :str = "postgresql://rag_user:rag_password@localhost:5432/rag_db"
    postgres_echo_sql: bool = False
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 0

    # OPENSEARCH CONFIG
    opensearch_host: str = "http://localhost:9200"


    # OLLAMA CONFIG
    ollama_host:str = "http://localhost:11434"
    ollama_models: Union[str, List[str]] = Field(default = ['llama3.2:1b','gemma3:1b'])
    ollama_default_model:str = "gemma3:1b"
    ollama_timeout: int = 300

    # ARXIV CONFIG
    arxiv : ArxivSettings = Field(default_factory=ArxivSettings)
    pdf_parser : PDFParserSettings = Field(default_factory=PDFParserSettings)


    @field_validator("ollama_models", mode="before")
    @classmethod
    def parse_ollama_models(cls, v):
        """
        parse comman separated string into list
        """
        if isinstance(v, str):
            return [model.strip() for model in v.split(",") if model.strip()]
        return v


def get_settings() -> Settings:
    """
    Get settings.
    """
    return Settings()
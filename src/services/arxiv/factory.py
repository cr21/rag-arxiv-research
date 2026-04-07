from src.config import get_settings
from .client import ArxivClient

def make_arxiv_client() -> ArxivClient:

    """

    Create and return an ArxivClient instance.
    """
    settings = get_settings()
    return ArxivClient(settings=settings.arxiv)
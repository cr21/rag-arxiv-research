from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ParserType(str, Enum):
    """
    Type of parser used to parse the paper.
    """
    DOCLING="docling"
    GROBID="grobid"

class PaperSection(BaseModel):
    title:str = Field(..., description="The title of the section.")
    content:str = Field(..., description="The content of the section.")
    level:int = Field(..., description="The level of the section.")

class PaperFigure(BaseModel):
    id:str = Field(..., description="The ID of the figure.")
    caption: str = Field(..., description="Figure caption")

class PaperTable(BaseModel):
    """Represents a table in a paper."""
    caption: str = Field(..., description="Table caption")
    id: str = Field(..., description="Table identifier")


class PdfContent(BaseModel):
    """PDF-specific content extracted by parsers like Docling."""
    sections: List[PaperSection] = Field(..., description="List of sections")
    figures: List[PaperFigure] = Field(default_factory=list, description="Figures")
    tables: List[PaperTable] = Field(default_factory=list, description="Tables")
    raw_text: str = Field(..., description="Full extracted text")
    references: List[str] = Field(default_factory=list, description="References")
    parser_used: ParserType = Field(..., description="Parser used for extraction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Parser metadata")


class ArxivMetadata(BaseModel):
    """Paper metadata from arXiv API."""
    title: str = Field(..., description="Paper title from arXiv")
    authors: List[str] = Field(..., description="Authors from arXiv")
    abstract: str = Field(..., description="Abstract from arXiv")
    arxiv_id: str = Field(..., description="arXiv identifier")
    categories: List[str] = Field(default_factory=list, description="arXiv categories")
    published_date: str = Field(..., description="Publication date")
    pdf_url: str = Field(..., description="PDF download URL")

class ParsedPaper(BaseModel):
    """Complete paper data combining arXiv metadata and PDF content."""
    arxiv_metadata: ArxivMetadata = Field(..., description="Metadata from arXiv API")
    pdf_content: Optional[PdfContent] = Field(None, description="Content extracted from PDF")

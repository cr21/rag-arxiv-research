from  pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

class ArxivPaper(BaseModel):
    """
    schema for Arxiv paper.
    """
    arxiv_id:str = Field(..., description="The Arxiv ID of the paper.")
    title:str = Field(..., description="The title of the paper.")
    authors:List[str] = Field(..., description="The authors of the paper.")
    abstract:str = Field(..., description="The abstract of the paper.")
    published_date:str = Field(..., description="The published date of the paper.")
    pdf_url:str = Field(..., description="The PDF URL of the paper.")
    categories:List[str] = Field(..., description="The categories of the paper.")

class PaperBase(BaseModel):
    """
    Core archive meta data Paper base.
    """
    arxiv_id:str = Field(..., description="The Arxiv ID of the paper.")
    title:str = Field(..., description="The title of the paper.")
    abstract:str = Field(..., description="The abstract of the paper.")
    authors:List[str] = Field(..., description="The authors of the paper.")
    published_date:str = Field(..., description="The published date of the paper.")
    pdf_url:str = Field(..., description="The PDF URL of the paper.")
    categories:List[str] = Field(..., description="The categories of the paper.")

class PaperCreate(PaperBase):
    """Schema for creating a paper with optional parsed content."""
    # Parsed PDF content optionally added when parsing is successful.
    raw_text : Optional[str] = Field(None, description="The raw text of the paper.")
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="List of sections with titles and contents")
    references: Optional[List[Dict[str, Any]]] = Field(None, description="List of references")

    # PDF processing metadata
    parser_used: Optional[str] = Field(None, description="The parser used to parse the paper.")
    parser_metadata: Optional[Dict[str, Any]] = Field(None, description="The metadata of the parser used to parse the paper.")
    pdf_processed: Optional[bool] = Field(None, description="Whether the PDF was processed successfully.")
    pdf_processing_date: Optional[datetime] = Field(None, description="The date and time the PDF was processed.")



class PaperResponse(PaperBase):
    """Schema for paper API responses with all content."""
    id:UUID = Field(..., description="The ID of the paper.")
    # Parsed PDF content (optional fields)
    raw_text: Optional[str] = Field(None, description="Full raw text extracted from PDF")
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="List of sections with titles and content")
    references: Optional[List[Dict[str, Any]]] = Field(None, description="List of references if extracted")

    # PDF processing metadata
    parser_used: Optional[str] = Field(None, description="Which parser was used")
    parser_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional parser metadata")
    pdf_processed: bool = Field(False, description="Whether PDF was successfully processed")
    pdf_processing_date: Optional[datetime] = Field(None, description="When PDF was processed")

    created_at:datetime = Field(..., description="The created at of the paper.")
    updated_at:datetime = Field(..., description="The updated at of the paper.")

    class Config:
        """
        Pydantic configurations
        """
        from_attributes = True

class PaperSearchResponse(BaseModel):
    """
    Paper search response.
    """
    total:int = Field(..., description="The total number of papers.")
    papers:List[PaperResponse] = Field(..., description="The list of papers.")
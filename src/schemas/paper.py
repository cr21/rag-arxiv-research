from  pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from datetime import datetime


class PaperBase(BaseModel):
    """
    Paper base.
    """
    arxive_id:str = Field(..., description="The Arxiv ID of the paper.")
    title:str = Field(..., description="The title of the paper.")
    abstract:str = Field(..., description="The abstract of the paper.")
    authors:List[str] = Field(..., description="The authors of the paper.")
    published_date:str = Field(..., description="The published date of the paper.")
    pdf_url:str = Field(..., description="The PDF URL of the paper.")
    categories:List[str] = Field(..., description="The categories of the paper.")

class PaperCreate(PaperBase):
    """
    Paper create.
    """
    pass


class PaperResponse(PaperBase):
    """
    Paper response.
    """
    id:UUID = Field(..., description="The ID of the paper.")
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
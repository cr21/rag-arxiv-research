from typing import List, Optional
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    """
    Request Schema for Asking questions about a paper.
    """
    question:str = Field(...,description="The question to ask about the paper.")

class PaperSource(BaseModel):
    """
    Schema for Paper Source information in response.
    """
    arxiv_id:str = Field(...,description="The Arxiv ID of the paper.")
    title:str = Field(...,description="The title of the paper.")
    authors:List[str] = Field(...,description="The authors of the paper.")
    abstract_preview:str = Field(...,description="The abstract preview of the paper.")

class AskResponse(BaseModel):
    answer:str = Field(...,description="The answer to the question.")
    paper_sources:List[PaperSource] = Field(...,description="The sources of the answer.")
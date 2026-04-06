from fastapi import APIRouter, Depends, HTTPException, Path
from src.schemas.paper import PaperResponse
from sqlalchemy.orm import Session
from src.dependencies import SessionDep
from src.repositories.paper import PaperRepository


router = APIRouter(prefix="/papers", tags=["Papers"])

@router.get("/{arxiv_id}", response_model=PaperResponse)
def get_paper_details(db:SessionDep,
 arxiv_id: str = Path(..., description="The Arxiv ID of the paper.")) -> PaperResponse:
    """
    Get the details of a paper by its Arxiv ID.
    """
    
    paper_repo = PaperRepository(db)
    paper = paper_repo.get_by_arxiv_id(arxiv_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperResponse.model_validate(paper)
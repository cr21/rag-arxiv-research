from fastapi import APIRouter, Depends, HTTPException, Path, Query
from src.schemas.arxiv.paper import PaperResponse, PaperSearchResponse
from sqlalchemy.orm import Session
from src.dependencies import SessionDep
from src.repositories.paper import PaperRepository


router = APIRouter(prefix="/papers", tags=["Papers"])



def list_papers(db:SessionDep,
limit:int =Query(default=10, ge=1, le=100, description="The number of papers to list."),
offset:int =Query(default=0, ge=0, description="The offset of the papers to list."),
):
    """
    List all papers from the arXiv API.
    """
    paper_repo  = PaperRepository(db)
    papers = paper_repo.get_all(limit=limit, offset=offset)
    total = paper_repo.get_count()

    return PaperSearchResponse(papers=[PaperResponse.model_validate(paper) for paper in papers], total=total)

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
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_session_id
from app.schemas.regulatory import KozakConfig, KozakResult, PromoterSearchResult, TerminatorSearchResult
from app.services import kozak_service, promoter_service, terminator_service

router = APIRouter()


@router.get("/promoters/search", response_model=PromoterSearchResult)
async def search_promoters(
    organism: str = Query(..., description="Target organism"),
    gene: str | None = Query(None, description="Gene name filter"),
    limit: int = Query(20, ge=1, le=100),
    session_id: str = Depends(get_session_id),
):
    return await promoter_service.search_promoters(organism, gene=gene, limit=limit)


@router.get("/promoters/{promoter_id}")
async def get_promoter(promoter_id: str, session_id: str = Depends(get_session_id)):
    return await promoter_service.get_promoter(promoter_id)


@router.get("/terminators/search", response_model=TerminatorSearchResult)
async def search_terminators(
    organism: str = Query(..., description="Target organism"),
    limit: int = Query(20, ge=1, le=100),
    session_id: str = Depends(get_session_id),
):
    return await terminator_service.search_terminators(organism, limit=limit)


@router.get("/terminators/{terminator_id}")
async def get_terminator(terminator_id: str, session_id: str = Depends(get_session_id)):
    return await terminator_service.get_terminator(terminator_id)


@router.post("/kozak", response_model=KozakResult)
async def generate_kozak(config: KozakConfig):
    result = kozak_service.generate_kozak(
        organism_tax_id=config.organism_tax_id,
        start_codon=config.start_codon,
    )
    return KozakResult(
        organism=result["organism"],
        consensus=result["consensus"],
        sequence=result["sequence"],
        notes=result["notes"],
    )

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_cache
from app.schemas.organism import CodonTableResponse, OrganismDetail, OrganismSearchResult
from app.services import organism_service
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/search", response_model=list[OrganismSearchResult])
async def search_organisms(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    return await organism_service.search_organisms(q, limit=limit)


@router.get("/{tax_id}", response_model=OrganismDetail)
async def get_organism(tax_id: int, cache: CacheService = Depends(get_cache)):
    return await organism_service.get_organism(tax_id, cache=cache)


@router.get("/{tax_id}/codon-table", response_model=CodonTableResponse)
async def get_codon_table(tax_id: int):
    return organism_service.get_codon_table(tax_id)

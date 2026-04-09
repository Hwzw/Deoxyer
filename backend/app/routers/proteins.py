from fastapi import APIRouter, Depends, Query

from app.dependencies import get_cache
from app.schemas.protein import ProteinDetail, ProteinSearchResult, ProteinSequence
from app.services import protein_service
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/search", response_model=list[ProteinSearchResult])
async def search_proteins(
    q: str = Query(..., description="Search query"),
    organism: str | None = Query(None, description="Filter by organism"),
    limit: int = Query(20, ge=1, le=100),
):
    return await protein_service.search_proteins(q, organism=organism, limit=limit)


@router.get("/{accession}", response_model=ProteinDetail)
async def get_protein(accession: str, cache: CacheService = Depends(get_cache)):
    return await protein_service.get_protein(accession, cache=cache)


@router.get("/{accession}/sequence", response_model=ProteinSequence)
async def get_protein_sequence(accession: str, cache: CacheService = Depends(get_cache)):
    return await protein_service.get_protein_sequence(accession, cache=cache)

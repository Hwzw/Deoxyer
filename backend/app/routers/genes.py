from fastapi import APIRouter, Depends, Query

from app.dependencies import get_cache
from app.schemas.gene import GeneDetail, GeneSearchResult, GeneSequence
from app.services import gene_service
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/search", response_model=list[GeneSearchResult])
async def search_genes(
    q: str = Query(..., description="Search query"),
    organism: str | None = Query(None, description="Filter by organism"),
    limit: int = Query(20, ge=1, le=100),
):
    return await gene_service.search_genes(q, organism=organism, limit=limit)


@router.get("/{gene_id}", response_model=GeneDetail)
async def get_gene(gene_id: str, cache: CacheService = Depends(get_cache)):
    return await gene_service.get_gene(gene_id, cache=cache)


@router.get("/{gene_id}/sequence", response_model=GeneSequence)
async def get_gene_sequence(
    gene_id: str,
    seq_type: str = Query("cds"),
    cache: CacheService = Depends(get_cache),
):
    return await gene_service.get_gene_sequence(gene_id, seq_type=seq_type, cache=cache)

"""Organism search and codon table retrieval."""

from __future__ import annotations

import python_codon_tables as pct
from fastapi import HTTPException

from app.clients import ncbi_client
from app.schemas.organism import CodonTableResponse, OrganismDetail, OrganismSearchResult
from app.services.cache_service import CacheService, TTL_ORGANISM


async def search_organisms(query: str, limit: int = 20) -> list[OrganismSearchResult]:
    results = await ncbi_client.search_taxonomy(query, limit=limit)
    tax_ids = results.get("IdList", [])

    organisms = []
    for tax_id in tax_ids:
        detail = await ncbi_client.fetch_taxonomy(tax_id)
        if detail:
            taxon = detail[0] if isinstance(detail, list) else detail
            organisms.append(
                OrganismSearchResult(
                    tax_id=int(tax_id),
                    scientific_name=taxon.get("ScientificName", ""),
                    common_name=taxon.get("CommonName"),
                    lineage=taxon.get("Lineage"),
                )
            )
    return organisms


async def get_organism(
    tax_id: int, cache: CacheService | None = None
) -> OrganismDetail:
    """Fetch organism details from NCBI Taxonomy."""
    cache_key = CacheService.make_key("organism", str(tax_id))
    if cache:
        try:
            cached = await cache.get_cached(cache_key)
            if cached:
                return OrganismDetail(**cached)
        except Exception:
            pass

    detail = await ncbi_client.fetch_taxonomy(str(tax_id))
    if not detail:
        raise HTTPException(status_code=404, detail=f"Organism with tax_id {tax_id} not found")

    taxon = detail[0] if isinstance(detail, list) else detail

    result = OrganismDetail(
        tax_id=int(tax_id),
        scientific_name=taxon.get("ScientificName", ""),
        common_name=taxon.get("CommonName") or None,
        lineage=taxon.get("Lineage") or None,
        gc_content=None,
    )

    if cache:
        try:
            await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_ORGANISM)
        except Exception:
            pass

    return result


def get_codon_table(tax_id: int) -> CodonTableResponse:
    """Get codon usage table. Tries python-codon-tables first."""
    available = pct.get_all_available_codons_tables()
    table_name = None
    for name in available:
        if str(tax_id) in name:
            table_name = name
            break

    if table_name:
        table = pct.get_codons_table(table_name)
    else:
        # Default to E. coli if organism not found
        table = pct.get_codons_table("e_coli_316407")

    return CodonTableResponse(
        organism_tax_id=tax_id,
        source="python-codon-tables",
        table=table,
    )

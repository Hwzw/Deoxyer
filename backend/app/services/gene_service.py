"""Gene search and retrieval service. Orchestrates NCBI client calls with Redis caching."""

from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

from app.clients import ncbi_client
from app.schemas.gene import GeneDetail, GeneSearchResult, GeneSequence
from app.services.cache_service import CacheService, TTL_GENE
from app.utils.fasta import parse_fasta


async def search_genes(
    query: str, organism: str | None = None, limit: int = 20
) -> list[GeneSearchResult]:
    results = await ncbi_client.search_genes(query, organism=organism, limit=limit)
    gene_ids = results.get("IdList", [])

    search_results = []
    for gene_id in gene_ids:
        summary = await ncbi_client.esummary(db="gene", id=gene_id)
        doc_sums = summary.get("DocumentSummarySet", {}).get("DocumentSummary", [])
        if doc_sums:
            doc = doc_sums[0]
            search_results.append(
                GeneSearchResult(
                    gene_id=gene_id,
                    symbol=doc.get("Name", ""),
                    description=doc.get("Description", ""),
                    organism=doc.get("Organism", {}).get("ScientificName", ""),
                    tax_id=doc.get("Organism", {}).get("TaxID"),
                )
            )
    return search_results


async def get_gene(
    gene_id: str, cache: CacheService | None = None
) -> GeneDetail:
    """Fetch detailed gene information from NCBI."""
    cache_key = CacheService.make_key("gene", gene_id)
    if cache:
        try:
            cached = await cache.get_cached(cache_key)
            if cached:
                return GeneDetail(**cached)
        except Exception:
            logger.warning("Cache operation failed", exc_info=True)

    summary = await ncbi_client.esummary(db="gene", id=gene_id)
    doc_sums = summary.get("DocumentSummarySet", {}).get("DocumentSummary", [])
    if not doc_sums:
        raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

    doc = doc_sums[0]
    organism_info = doc.get("Organism", {})
    other_aliases = doc.get("OtherAliases", "")

    result = GeneDetail(
        gene_id=gene_id,
        symbol=doc.get("Name", ""),
        full_name=doc.get("Description", ""),
        description=doc.get("Summary", doc.get("Description", "")),
        organism=organism_info.get("ScientificName", ""),
        tax_id=int(organism_info.get("TaxID", 0)),
        chromosome=doc.get("Chromosome") or None,
        map_location=doc.get("MapLocation") or None,
        aliases=other_aliases.split(", ") if other_aliases else [],
    )

    if cache:
        try:
            await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_GENE)
        except Exception:
            logger.warning("Cache operation failed", exc_info=True)

    return result


async def get_gene_sequence(
    gene_id: str, seq_type: str = "cds", cache: CacheService | None = None
) -> GeneSequence:
    """Fetch gene coding sequence from NCBI Nucleotide."""
    cache_key = CacheService.make_key("gene_seq", f"{gene_id}:{seq_type}")
    if cache:
        try:
            cached = await cache.get_cached(cache_key)
            if cached:
                return GeneSequence(**cached)
        except Exception:
            logger.warning("Cache operation failed", exc_info=True)

    # Fetch FASTA text for this gene ID from NCBI Nucleotide
    try:
        fasta_text = await ncbi_client.fetch_nucleotide_text(gene_id, rettype="fasta")
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Sequence not found for gene {gene_id}"
        ) from exc

    parsed = parse_fasta(fasta_text)
    if not parsed:
        raise HTTPException(
            status_code=404, detail=f"Sequence not found for gene {gene_id}"
        )

    sequence = parsed[0]["sequence"]
    header = parsed[0].get("header", "")
    # Try to extract accession from FASTA header (e.g. ">NM_000546.6 ...")
    accession = header.split()[0] if header else gene_id

    result = GeneSequence(
        gene_id=gene_id,
        accession=accession,
        sequence=sequence,
        sequence_type=seq_type,
        length=len(sequence),
    )

    if cache:
        try:
            await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_GENE)
        except Exception:
            logger.warning("Cache operation failed", exc_info=True)

    return result

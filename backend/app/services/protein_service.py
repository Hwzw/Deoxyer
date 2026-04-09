"""Protein search and retrieval. Tries UniProt first, falls back to NCBI Protein."""

from __future__ import annotations

from fastapi import HTTPException

from app.clients import ncbi_client
from app.clients.uniprot_client import uniprot_client
from app.schemas.protein import ProteinDetail, ProteinSearchResult, ProteinSequence
from app.services.cache_service import CacheService, TTL_PROTEIN
from app.utils.fasta import parse_fasta


async def search_proteins(
    query: str, organism: str | None = None, limit: int = 20
) -> list[ProteinSearchResult]:
    """Search UniProt first, then NCBI Protein."""
    results = []

    # Try UniProt
    try:
        uniprot_data = await uniprot_client.search_proteins(query, organism=organism, limit=limit)
        for entry in uniprot_data.get("results", []):
            results.append(
                ProteinSearchResult(
                    accession=entry.get("primaryAccession", ""),
                    name=entry.get("proteinDescription", {})
                    .get("recommendedName", {})
                    .get("fullName", {})
                    .get("value", ""),
                    organism=entry.get("organism", {}).get("scientificName", ""),
                    length=entry.get("sequence", {}).get("length", 0),
                    source="uniprot",
                )
            )
    except Exception:
        pass  # Fall through to NCBI

    # Supplement with NCBI if needed
    if len(results) < limit:
        try:
            ncbi_data = await ncbi_client.search_proteins(
                query, organism=organism, limit=limit - len(results)
            )
            for protein_id in ncbi_data.get("IdList", []):
                summary = await ncbi_client.esummary(db="protein", id=protein_id)
                doc_sums = summary.get("DocumentSummarySet", {}).get("DocumentSummary", [])
                if doc_sums:
                    doc = doc_sums[0]
                    results.append(
                        ProteinSearchResult(
                            accession=doc.get("AccessionVersion", doc.get("Caption", protein_id)),
                            name=doc.get("Title", ""),
                            organism=doc.get("Organism", ""),
                            length=int(doc.get("Slen", 0)),
                            source="ncbi",
                        )
                    )
        except Exception:
            pass
    return results


def _extract_function(uniprot_entry: dict) -> str | None:
    """Extract function annotation from UniProt comment section."""
    for comment in uniprot_entry.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                return texts[0].get("value")
    return None


def _extract_tax_id_from_ncbi_protein(record: dict) -> int | None:
    """Extract taxonomy ID from NCBI GenBank protein record features."""
    for feature in record.get("GBSeq_feature-table", []):
        if feature.get("GBFeature_key") == "source":
            for qual in feature.get("GBFeature_quals", []):
                if qual.get("GBQualifier_name") == "db_xref":
                    val = qual.get("GBQualifier_value", "")
                    if val.startswith("taxon:"):
                        return int(val.replace("taxon:", ""))
    return None


async def get_protein(
    accession: str, cache: CacheService | None = None
) -> ProteinDetail:
    """Fetch protein detail from UniProt or NCBI."""
    cache_key = CacheService.make_key("protein", accession)
    if cache:
        try:
            cached = await cache.get_cached(cache_key)
            if cached:
                return ProteinDetail(**cached)
        except Exception:
            pass

    # Try UniProt first
    try:
        entry = await uniprot_client.get_entry(accession)
        protein_desc = entry.get("proteinDescription", {})
        rec_name = protein_desc.get("recommendedName", {})
        sub_names = protein_desc.get("submissionNames", [])

        name = rec_name.get("fullName", {}).get("value", "")
        if not name and sub_names:
            name = sub_names[0].get("fullName", {}).get("value", "")

        short_names = rec_name.get("shortNames", [])
        short_name = short_names[0].get("value", "") if short_names else ""

        gene_names = entry.get("genes", [])
        gene_name = gene_names[0].get("geneName", {}).get("value") if gene_names else None

        organism_data = entry.get("organism", {})

        result = ProteinDetail(
            accession=entry.get("primaryAccession", accession),
            name=short_name or name,
            full_name=name,
            organism=organism_data.get("scientificName", ""),
            tax_id=organism_data.get("taxonId"),
            length=entry.get("sequence", {}).get("length", 0),
            function=_extract_function(entry),
            gene_name=gene_name,
            source="uniprot",
        )

        if cache:
            try:
                await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_PROTEIN)
            except Exception:
                pass
        return result
    except Exception:
        pass  # Fall through to NCBI

    # NCBI fallback
    try:
        ncbi_data = await ncbi_client.fetch_protein(accession)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Protein {accession} not found") from exc

    if not ncbi_data:
        raise HTTPException(status_code=404, detail=f"Protein {accession} not found")

    record = ncbi_data[0] if isinstance(ncbi_data, list) else ncbi_data

    result = ProteinDetail(
        accession=accession,
        name=record.get("GBSeq_definition", ""),
        full_name=record.get("GBSeq_definition", ""),
        organism=record.get("GBSeq_organism", ""),
        tax_id=_extract_tax_id_from_ncbi_protein(record),
        length=int(record.get("GBSeq_length", 0)),
        function=None,
        gene_name=None,
        source="ncbi",
    )

    if cache:
        try:
            await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_PROTEIN)
        except Exception:
            pass
    return result


async def get_protein_sequence(
    accession: str, cache: CacheService | None = None
) -> ProteinSequence:
    """Fetch protein amino acid sequence."""
    cache_key = CacheService.make_key("protein_seq", accession)
    if cache:
        try:
            cached = await cache.get_cached(cache_key)
            if cached:
                return ProteinSequence(**cached)
        except Exception:
            pass

    # Try UniProt FASTA first
    try:
        fasta_text = await uniprot_client.get_fasta(accession)
        parsed = parse_fasta(fasta_text)
        if parsed:
            sequence = parsed[0]["sequence"]
            result = ProteinSequence(
                accession=accession,
                sequence=sequence,
                length=len(sequence),
                source="uniprot",
            )
            if cache:
                try:
                    await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_PROTEIN)
                except Exception:
                    pass
            return result
    except Exception:
        pass

    # NCBI fallback
    try:
        ncbi_data = await ncbi_client.fetch_protein(accession)
    except Exception as exc:
        raise HTTPException(
            status_code=404, detail=f"Protein sequence {accession} not found"
        ) from exc

    if not ncbi_data:
        raise HTTPException(status_code=404, detail=f"Protein sequence {accession} not found")

    record = ncbi_data[0] if isinstance(ncbi_data, list) else ncbi_data
    sequence = record.get("GBSeq_sequence", "").upper()

    if not sequence:
        raise HTTPException(status_code=404, detail=f"Protein sequence {accession} not found")

    result = ProteinSequence(
        accession=accession,
        sequence=sequence,
        length=len(sequence),
        source="ncbi",
    )

    if cache:
        try:
            await cache.set_cached(cache_key, result.model_dump(mode="json"), ttl=TTL_PROTEIN)
        except Exception:
            pass
    return result

"""NCBI Entrez API client using Biopython.

Handles Gene, Protein, Nucleotide, and Taxonomy databases.
Rate limited to 10 requests/sec with API key, 3/sec without.
"""

import asyncio
from functools import partial

from Bio import Entrez

from app.config import settings

# Configure Entrez
Entrez.email = settings.NCBI_EMAIL
if settings.NCBI_API_KEY:
    Entrez.api_key = settings.NCBI_API_KEY

# Rate limiting semaphore
_max_concurrent = settings.NCBI_CONCURRENT_WITH_KEY if settings.NCBI_API_KEY else settings.NCBI_CONCURRENT_WITHOUT_KEY
_semaphore = asyncio.Semaphore(_max_concurrent)


async def _run_entrez(func, **kwargs):
    """Run a Biopython Entrez function in a thread pool with rate limiting."""
    async with _semaphore:
        loop = asyncio.get_event_loop()
        handle = await loop.run_in_executor(None, partial(func, **kwargs))
        result = await loop.run_in_executor(None, Entrez.read, handle)
        return result


async def esearch(db: str, term: str, retmax: int = 20) -> dict:
    return await _run_entrez(Entrez.esearch, db=db, term=term, retmax=retmax)


async def efetch(db: str, id: str, rettype: str = "gb", retmode: str = "xml") -> dict:
    return await _run_entrez(Entrez.efetch, db=db, id=id, rettype=rettype, retmode=retmode)


async def esummary(db: str, id: str) -> dict:
    return await _run_entrez(Entrez.esummary, db=db, id=id)


async def search_genes(query: str, organism: str | None = None, limit: int = 20) -> dict:
    term = query
    if organism:
        term = f"{query} AND {organism}[Organism]"
    return await esearch(db="gene", term=term, retmax=limit)


async def search_proteins(query: str, organism: str | None = None, limit: int = 20) -> dict:
    term = query
    if organism:
        term = f"{query} AND {organism}[Organism]"
    return await esearch(db="protein", term=term, retmax=limit)


async def search_taxonomy(query: str, limit: int = 20) -> dict:
    return await esearch(db="taxonomy", term=query, retmax=limit)


async def fetch_gene(gene_id: str) -> dict:
    return await efetch(db="gene", id=gene_id, rettype="gene_table", retmode="xml")


async def fetch_protein(protein_id: str) -> dict:
    return await efetch(db="protein", id=protein_id, rettype="gp", retmode="xml")


async def fetch_nucleotide(accession: str, rettype: str = "fasta") -> dict:
    return await efetch(db="nucleotide", id=accession, rettype=rettype, retmode="text")


async def fetch_nucleotide_text(accession: str, rettype: str = "fasta") -> str:
    """Fetch nucleotide sequence as raw text (for FASTA parsing).

    Unlike fetch_nucleotide, this does NOT pass through Entrez.read(),
    which fails on plain-text formats like FASTA.
    """
    async with _semaphore:
        loop = asyncio.get_event_loop()
        handle = await loop.run_in_executor(
            None, partial(Entrez.efetch, db="nucleotide", id=accession, rettype=rettype, retmode="text")
        )
        text = await loop.run_in_executor(None, handle.read)
        return text


async def fetch_taxonomy(tax_id: str) -> dict:
    return await efetch(db="taxonomy", id=tax_id)

from pydantic import BaseModel


class OrganismSearchResult(BaseModel):
    tax_id: int
    scientific_name: str
    common_name: str | None = None
    lineage: str | None = None


class OrganismDetail(BaseModel):
    tax_id: int
    scientific_name: str
    common_name: str | None = None
    lineage: str | None = None
    gc_content: float | None = None


class CodonTableResponse(BaseModel):
    organism_tax_id: int
    source: str
    table: dict[str, dict[str, float]]  # amino_acid -> {codon: frequency}
    is_fallback: bool = False
    notes: str | None = None

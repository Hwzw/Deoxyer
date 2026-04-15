from pydantic import BaseModel


class PromoterInfo(BaseModel):
    id: str
    name: str
    organism: str
    sequence: str
    length: int
    description: str | None = None
    strength: str | None = None  # "weak", "moderate", "strong"


class PromoterSearchResult(BaseModel):
    promoters: list[PromoterInfo]
    total: int
    message: str | None = None


class KozakConfig(BaseModel):
    organism_tax_id: int
    start_codon: str = "ATG"
    custom_context: str | None = None  # override default Kozak for organism


class KozakResult(BaseModel):
    organism: str
    consensus: str  # e.g. "GCCACCATGG"
    sequence: str  # the actual Kozak + start codon to insert
    notes: str | None = None

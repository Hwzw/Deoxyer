from pydantic import BaseModel


class MiscSequenceInfo(BaseModel):
    id: str
    name: str
    category: str | None = None
    subtype: str | None = None
    sequence_type: str  # "protein" or "dna"
    sequence: str
    length: int
    notes: str | None = None


class MiscSearchResult(BaseModel):
    items: list[MiscSequenceInfo]
    total: int
    message: str | None = None

from typing import Literal

from pydantic import BaseModel, Field

from app.models.construct_element import ElementType


WorkspaceItemType = Literal[
    "dna",
    "protein",
    "cds",
    "promoter",
    "terminator",
    "kozak",
    "custom",
]

WorkspaceItemSource = Literal[
    "ncbi-gene",
    "uniprot",
    "manual",
    "optimized",
    "generated",
    "promoter-db",
    "terminator-db",
    "slice",
]


class WorkspaceItemSchema(BaseModel):
    type: WorkspaceItemType
    sequence: str = Field(..., max_length=100_000)
    length: int
    source: WorkspaceItemSource
    label: str = Field(..., max_length=255)
    accession: str | None = None
    cai_before: float | None = None
    cai_after: float | None = None
    gc_content: float | None = None
    consensus: str | None = None
    strength: str | None = None
    notes: str | None = None


WORKSPACE_TYPE_TO_ELEMENT_TYPE: dict[WorkspaceItemType, ElementType] = {
    "promoter": ElementType.PROMOTER,
    "terminator": ElementType.TERMINATOR,
    "kozak": ElementType.KOZAK,
    "cds": ElementType.CDS,
    "dna": ElementType.CDS,
    "protein": ElementType.CDS,
    "custom": ElementType.CUSTOM,
}

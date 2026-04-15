import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.construct_element import ElementType


class ConstructElementSchema(BaseModel):
    element_type: ElementType
    label: str = Field(..., max_length=255)
    sequence: str = Field(..., max_length=100_000)
    position: int
    metadata_json: dict | None = None


class ConstructCreate(BaseModel):
    project_id: uuid.UUID
    name: str = Field(..., max_length=255)
    organism_tax_id: int | None = None
    elements: list[ConstructElementSchema] = []


class ConstructUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    organism_tax_id: int | None = None
    elements: list[ConstructElementSchema] | None = None


class ConstructResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    full_sequence: str | None
    organism_tax_id: int | None
    elements: list[ConstructElementSchema]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

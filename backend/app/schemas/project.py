import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.construct import ConstructResponse


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=2000)


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    constructs: list[ConstructResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int

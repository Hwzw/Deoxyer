import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_session_id
from app.models.project import Project
from app.schemas.construct import ConstructCreate, ConstructElementSchema, ConstructResponse, ConstructUpdate
from app.services import construct_assembly_service, construct_service

router = APIRouter()


async def _verify_project_session(db: AsyncSession, project_id: uuid.UUID, session_id: str) -> Project:
    """Verify the project exists and belongs to this session."""
    project = await db.get(Project, project_id)
    if not project or project.session_id != session_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _verify_construct_session(db: AsyncSession, construct_id: uuid.UUID, session_id: str):
    """Verify the construct's parent project belongs to this session."""
    construct = await construct_service.get_construct(db, construct_id)
    if not construct:
        raise HTTPException(status_code=404, detail="Construct not found")
    await _verify_project_session(db, construct.project_id, session_id)
    return construct


@router.get("/", response_model=list[ConstructResponse])
async def list_constructs(
    project_id: uuid.UUID = Query(..., description="Filter by project"),
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    await _verify_project_session(db, project_id, session_id)
    return await construct_service.list_constructs(db, project_id)


@router.post("/", response_model=ConstructResponse)
async def create_construct(
    data: ConstructCreate,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    await _verify_project_session(db, data.project_id, session_id)
    return await construct_service.create_construct(db, data)


@router.get("/{construct_id}", response_model=ConstructResponse)
async def get_construct(
    construct_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    construct = await _verify_construct_session(db, construct_id, session_id)
    return construct


@router.put("/{construct_id}", response_model=ConstructResponse)
async def update_construct(
    construct_id: uuid.UUID,
    data: ConstructUpdate,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    await _verify_construct_session(db, construct_id, session_id)
    construct = await construct_service.update_construct(db, construct_id, data)
    if not construct:
        raise HTTPException(status_code=404, detail="Construct not found")
    return construct


@router.delete("/{construct_id}")
async def delete_construct(
    construct_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    await _verify_construct_session(db, construct_id, session_id)
    deleted = await construct_service.delete_construct(db, construct_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Construct not found")
    return {"status": "deleted"}


@router.post("/{construct_id}/assemble")
async def assemble_construct(
    construct_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id),
):
    construct = await _verify_construct_session(db, construct_id, session_id)
    elements = [
        ConstructElementSchema.model_validate(e, from_attributes=True) for e in construct.elements
    ]
    return construct_assembly_service.assemble_construct(elements)

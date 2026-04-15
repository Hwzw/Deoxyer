"""Project CRUD operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.construct import Construct
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def list_projects(db: AsyncSession, session_id: str) -> list[Project]:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.constructs).selectinload(Construct.elements))
        .where(Project.session_id == session_id)
        .order_by(Project.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_project(db: AsyncSession, project_id: uuid.UUID, session_id: str) -> Project | None:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.constructs).selectinload(Construct.elements))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project and project.session_id != session_id:
        return None
    return project


async def create_project(db: AsyncSession, data: ProjectCreate, session_id: str) -> Project:
    project = Project(name=data.name, description=data.description, session_id=session_id)
    db.add(project)
    await db.commit()
    await db.refresh(project, attribute_names=["constructs"])
    return project


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, data: ProjectUpdate, session_id: str
) -> Project | None:
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.constructs).selectinload(Construct.elements))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project or project.session_id != session_id:
        return None
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    await db.commit()
    await db.refresh(project, attribute_names=["constructs"])
    return project


async def delete_project(db: AsyncSession, project_id: uuid.UUID, session_id: str) -> bool:
    project = await db.get(Project, project_id)
    if not project or project.session_id != session_id:
        return False
    await db.delete(project)
    await db.commit()
    return True

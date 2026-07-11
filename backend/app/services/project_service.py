import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

DUPLICATE_NAME_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="A project with this name already exists"
)


async def create_project(
    db: AsyncSession, organization_id: uuid.UUID, data: ProjectCreate, creator_id: uuid.UUID
) -> Project:
    project = Project(
        organization_id=organization_id,
        name=data.name,
        description=data.description,
        created_by=creator_id,
    )
    db.add(project)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_NAME_ERROR from exc
    await db.refresh(project)
    return project


async def list_projects(db: AsyncSession, organization_id: uuid.UUID) -> list[Project]:
    result = await db.execute(select(Project).where(Project.organization_id == organization_id))
    return list(result.scalars().all())


async def update_project(db: AsyncSession, project: Project, data: ProjectUpdate) -> Project:
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_NAME_ERROR from exc
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.commit()

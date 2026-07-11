from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.db import get_db
from app.core.deps import (
    OrgContext,
    ProjectContext,
    get_current_user,
    get_org_context,
    get_project_context,
    require_project_role,
    require_role,
)
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services import project_service

router = APIRouter(tags=["projects"])


@router.post(
    "/organizations/{organization_id}/projects",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    data: ProjectCreate,
    ctx: OrgContext = Depends(require_role(Role.ADMIN, Role.EDITOR)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    return await project_service.create_project(db, ctx.organization.id, data, current_user.id)


@router.get("/organizations/{organization_id}/projects", response_model=list[ProjectOut])
async def list_projects(
    ctx: OrgContext = Depends(get_org_context), db: AsyncSession = Depends(get_db)
) -> list[ProjectOut]:
    return await project_service.list_projects(db, ctx.organization.id)


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(ctx: ProjectContext = Depends(get_project_context)) -> ProjectOut:
    return ctx.project


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    data: ProjectUpdate,
    ctx: ProjectContext = Depends(require_project_role(Role.ADMIN, Role.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> ProjectOut:
    return await project_service.update_project(db, ctx.project, data)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    ctx: ProjectContext = Depends(require_project_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await project_service.delete_project(db, ctx.project)

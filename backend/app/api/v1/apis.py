from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.db import get_db
from app.core.deps import (
    ApiContext,
    ProjectContext,
    get_api_context,
    get_project_context,
    require_api_role,
    require_project_role,
)
from app.schemas.api_registry import ApiCreate, ApiOut, ApiUpdate
from app.services import api_registry_service

router = APIRouter(tags=["apis"])


@router.post("/projects/{project_id}/apis", response_model=ApiOut, status_code=status.HTTP_201_CREATED)
async def create_api(
    data: ApiCreate,
    ctx: ProjectContext = Depends(require_project_role(Role.ADMIN, Role.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> ApiOut:
    return await api_registry_service.create_api(db, ctx.organization.id, ctx.project.id, data)


@router.get("/projects/{project_id}/apis", response_model=list[ApiOut])
async def list_apis(
    ctx: ProjectContext = Depends(get_project_context), db: AsyncSession = Depends(get_db)
) -> list[ApiOut]:
    return await api_registry_service.list_apis(db, ctx.project.id)


@router.get("/apis/{api_id}", response_model=ApiOut)
async def get_api(ctx: ApiContext = Depends(get_api_context)) -> ApiOut:
    return ctx.api


@router.patch("/apis/{api_id}", response_model=ApiOut)
async def update_api(
    data: ApiUpdate,
    ctx: ApiContext = Depends(require_api_role(Role.ADMIN, Role.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> ApiOut:
    return await api_registry_service.update_api(db, ctx.organization.id, ctx.api, data)


@router.delete("/apis/{api_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api(
    ctx: ApiContext = Depends(require_api_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await api_registry_service.delete_api(db, ctx.api)

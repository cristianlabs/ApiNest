from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.db import get_db
from app.core.deps import (
    ApiContext,
    EndpointContext,
    get_api_context,
    get_endpoint_context,
    require_api_role,
    require_endpoint_role,
)
from app.schemas.endpoint import EndpointCreate, EndpointOut, EndpointUpdate
from app.services import endpoint_service

router = APIRouter(tags=["endpoints"])


@router.post(
    "/apis/{api_id}/endpoints", response_model=EndpointOut, status_code=status.HTTP_201_CREATED
)
async def create_endpoint(
    data: EndpointCreate,
    ctx: ApiContext = Depends(require_api_role(Role.ADMIN, Role.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> EndpointOut:
    return await endpoint_service.create_endpoint(db, ctx.api.id, data)


@router.get("/apis/{api_id}/endpoints", response_model=list[EndpointOut])
async def list_endpoints(
    ctx: ApiContext = Depends(get_api_context), db: AsyncSession = Depends(get_db)
) -> list[EndpointOut]:
    return await endpoint_service.list_endpoints(db, ctx.api.id)


@router.get("/endpoints/{endpoint_id}", response_model=EndpointOut)
async def get_endpoint(ctx: EndpointContext = Depends(get_endpoint_context)) -> EndpointOut:
    return ctx.endpoint


@router.patch("/endpoints/{endpoint_id}", response_model=EndpointOut)
async def update_endpoint(
    data: EndpointUpdate,
    ctx: EndpointContext = Depends(require_endpoint_role(Role.ADMIN, Role.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> EndpointOut:
    return await endpoint_service.update_endpoint(db, ctx.endpoint, data)


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    ctx: EndpointContext = Depends(require_endpoint_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await endpoint_service.delete_endpoint(db, ctx.endpoint)

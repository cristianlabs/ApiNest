import httpx
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.db import get_db
from app.core.deps import (
    HistoryContext,
    ProjectContext,
    get_current_user,
    get_history_context,
    get_http_client,
    get_project_context,
    require_project_role,
)
from app.models.user import User
from app.schemas.common import Page
from app.schemas.rest_client import FavoriteUpdate, RequestHistoryOut, SendRequestPayload
from app.services import rest_client_service

router = APIRouter(tags=["rest-client"])


@router.post(
    "/projects/{project_id}/rest-client/send",
    response_model=RequestHistoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_request(
    payload: SendRequestPayload,
    ctx: ProjectContext = Depends(require_project_role(Role.ADMIN, Role.EDITOR)),
    current_user: User = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db),
) -> RequestHistoryOut:
    return await rest_client_service.send_request(
        db, http_client, ctx.project.id, current_user.id, payload
    )


@router.get(
    "/projects/{project_id}/rest-client/history", response_model=Page[RequestHistoryOut]
)
async def list_history(
    ctx: ProjectContext = Depends(get_project_context),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[RequestHistoryOut]:
    items, total = await rest_client_service.list_history(db, ctx.project.id, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/rest-client/history/{history_id}", response_model=RequestHistoryOut)
async def get_history_entry(ctx: HistoryContext = Depends(get_history_context)) -> RequestHistoryOut:
    return ctx.history


@router.patch("/rest-client/history/{history_id}/favorite", response_model=RequestHistoryOut)
async def set_favorite(
    data: FavoriteUpdate,
    ctx: HistoryContext = Depends(get_history_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RequestHistoryOut:
    return await rest_client_service.set_favorite(
        db, ctx.history, ctx.membership, current_user, data.is_favorite
    )


@router.delete("/rest-client/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_entry(
    ctx: HistoryContext = Depends(get_history_context),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await rest_client_service.delete_history(db, ctx.history, ctx.membership, current_user)

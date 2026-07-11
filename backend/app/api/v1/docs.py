from fastapi import APIRouter, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ApiContext, get_api_context
from app.services import openapi_export_service

router = APIRouter(tags=["docs"])


@router.get("/apis/{api_id}/openapi.json")
async def get_api_openapi_spec(
    ctx: ApiContext = Depends(get_api_context), db: AsyncSession = Depends(get_db)
) -> dict:
    return await openapi_export_service.build_openapi_spec(db, ctx.api)


@router.get("/apis/{api_id}/docs", response_class=HTMLResponse, include_in_schema=False)
async def get_api_docs(ctx: ApiContext = Depends(get_api_context)) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=f"/api/v1/apis/{ctx.api.id}/openapi.json",
        title=f"{ctx.api.name} — Docs",
    )

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_registry import Api
from app.schemas.api_registry import ApiCreate, ApiUpdate

DUPLICATE_NAME_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="An API with this name already exists in the project"
)


async def create_api(db: AsyncSession, project_id: uuid.UUID, data: ApiCreate) -> Api:
    api = Api(project_id=project_id, **data.model_dump())
    db.add(api)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_NAME_ERROR from exc
    await db.refresh(api)
    return api


async def list_apis(db: AsyncSession, project_id: uuid.UUID) -> list[Api]:
    result = await db.execute(select(Api).where(Api.project_id == project_id))
    return list(result.scalars().all())


async def update_api(db: AsyncSession, api: Api, data: ApiUpdate) -> Api:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(api, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_NAME_ERROR from exc
    await db.refresh(api)
    return api


async def delete_api(db: AsyncSession, api: Api) -> None:
    await db.delete(api)
    await db.commit()

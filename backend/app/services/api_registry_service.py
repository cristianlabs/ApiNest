import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_registry import Api
from app.models.organization import Membership
from app.schemas.api_registry import ApiCreate, ApiUpdate

DUPLICATE_NAME_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail="An API with this name already exists in the project"
)
INVALID_OWNER_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST, detail="owner_id must be a member of the organization"
)


async def _validate_owner(
    db: AsyncSession, organization_id: uuid.UUID, owner_id: uuid.UUID | None
) -> None:
    if owner_id is None:
        return
    result = await db.execute(
        select(Membership).where(
            Membership.organization_id == organization_id, Membership.user_id == owner_id
        )
    )
    if result.scalar_one_or_none() is None:
        raise INVALID_OWNER_ERROR


async def create_api(
    db: AsyncSession, organization_id: uuid.UUID, project_id: uuid.UUID, data: ApiCreate
) -> Api:
    await _validate_owner(db, organization_id, data.owner_id)
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


async def update_api(db: AsyncSession, organization_id: uuid.UUID, api: Api, data: ApiUpdate) -> Api:
    update_data = data.model_dump(exclude_unset=True)
    if "owner_id" in update_data:
        await _validate_owner(db, organization_id, update_data["owner_id"])
    for field, value in update_data.items():
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

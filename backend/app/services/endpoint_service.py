import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_registry import Endpoint
from app.schemas.endpoint import EndpointCreate, EndpointUpdate

DUPLICATE_ENDPOINT_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="An endpoint with this method and path already exists for this API",
)


async def create_endpoint(db: AsyncSession, api_id: uuid.UUID, data: EndpointCreate) -> Endpoint:
    endpoint = Endpoint(api_id=api_id, **data.model_dump())
    db.add(endpoint)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_ENDPOINT_ERROR from exc
    await db.refresh(endpoint)
    return endpoint


async def list_endpoints(db: AsyncSession, api_id: uuid.UUID) -> list[Endpoint]:
    result = await db.execute(select(Endpoint).where(Endpoint.api_id == api_id))
    return list(result.scalars().all())


async def update_endpoint(db: AsyncSession, endpoint: Endpoint, data: EndpointUpdate) -> Endpoint:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(endpoint, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_ENDPOINT_ERROR from exc
    await db.refresh(endpoint)
    return endpoint


async def delete_endpoint(db: AsyncSession, endpoint: Endpoint) -> None:
    await db.delete(endpoint)
    await db.commit()

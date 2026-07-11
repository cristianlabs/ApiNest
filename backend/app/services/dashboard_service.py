import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MembershipStatus
from app.models.api_registry import Api, Endpoint
from app.models.organization import Membership
from app.models.project import Project
from app.models.request_history import RequestHistory
from app.models.user import User

RECENT_REQUESTS_LIMIT = 10
API_STATUS_LIMIT = 20

EMPTY_SUMMARY = {
    "organizations_count": 0,
    "projects_count": 0,
    "apis_count": 0,
    "endpoints_count": 0,
    "recent_requests": [],
    "api_statuses": [],
}


async def _user_organization_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.execute(
        select(Membership.organization_id).where(
            Membership.user_id == user_id, Membership.status == MembershipStatus.ACTIVE
        )
    )
    return [row[0] for row in result.all()]


async def _count(db: AsyncSession, model, column, values: list) -> int:
    if not values:
        return 0
    result = await db.execute(select(func.count()).select_from(model).where(column.in_(values)))
    return result.scalar_one()


async def _last_status_per_api(db: AsyncSession, project_ids: list[uuid.UUID]) -> list[dict]:
    # Postgres-specific DISTINCT ON: for each api_id, keep only the most recent
    # RequestHistory row (ordering within each group by created_at desc).
    latest_per_api = (
        select(
            RequestHistory.api_id,
            RequestHistory.response_status_code,
            RequestHistory.error,
            RequestHistory.created_at,
        )
        .where(RequestHistory.project_id.in_(project_ids), RequestHistory.api_id.isnot(None))
        .distinct(RequestHistory.api_id)
        .order_by(RequestHistory.api_id, RequestHistory.created_at.desc())
        .subquery()
    )
    result = await db.execute(
        select(
            Api.id,
            Api.name,
            latest_per_api.c.response_status_code,
            latest_per_api.c.error,
            latest_per_api.c.created_at,
        )
        .join(latest_per_api, latest_per_api.c.api_id == Api.id)
        .order_by(latest_per_api.c.created_at.desc())
        .limit(API_STATUS_LIMIT)
    )
    return [
        {
            "api_id": row.id,
            "api_name": row.name,
            "last_status_code": row.response_status_code,
            "last_error": row.error,
            "last_checked_at": row.created_at,
        }
        for row in result.all()
    ]


async def get_summary(db: AsyncSession, user: User) -> dict:
    org_ids = await _user_organization_ids(db, user.id)
    if not org_ids:
        return dict(EMPTY_SUMMARY)

    projects_count = await _count(db, Project, Project.organization_id, org_ids)

    project_ids = [
        row[0]
        for row in (
            await db.execute(select(Project.id).where(Project.organization_id.in_(org_ids)))
        ).all()
    ]
    if not project_ids:
        return {**EMPTY_SUMMARY, "organizations_count": len(org_ids)}

    apis_count = await _count(db, Api, Api.project_id, project_ids)

    api_ids = [
        row[0] for row in (await db.execute(select(Api.id).where(Api.project_id.in_(project_ids)))).all()
    ]
    endpoints_count = await _count(db, Endpoint, Endpoint.api_id, api_ids)

    recent_result = await db.execute(
        select(RequestHistory)
        .where(RequestHistory.project_id.in_(project_ids))
        .order_by(RequestHistory.created_at.desc())
        .limit(RECENT_REQUESTS_LIMIT)
    )
    recent_requests = list(recent_result.scalars().all())

    api_statuses = await _last_status_per_api(db, project_ids)

    return {
        "organizations_count": len(org_ids),
        "projects_count": projects_count,
        "apis_count": apis_count,
        "endpoints_count": endpoints_count,
        "recent_requests": recent_requests,
        "api_statuses": api_statuses,
    }

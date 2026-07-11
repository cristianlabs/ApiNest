import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MembershipStatus, Role
from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.api_registry import Api, Endpoint
from app.models.organization import Membership, Organization
from app.models.project import Project
from app.models.user import User
from app.services.user_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
)
NOT_A_MEMBER_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization"
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise CREDENTIALS_ERROR

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise CREDENTIALS_ERROR

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


async def _get_active_membership(
    db: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID
) -> Membership:
    result = await db.execute(
        select(Membership).where(
            Membership.organization_id == organization_id, Membership.user_id == user_id
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None or membership.status != MembershipStatus.ACTIVE:
        raise NOT_A_MEMBER_ERROR
    return membership


@dataclass
class OrgContext:
    organization: Organization
    membership: Membership


async def get_org_context(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrgContext:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    membership = await _get_active_membership(db, organization_id, current_user.id)
    return OrgContext(organization=organization, membership=membership)


def require_role(*roles: Role):
    async def checker(ctx: OrgContext = Depends(get_org_context)) -> OrgContext:
        if ctx.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action"
            )
        return ctx

    return checker


@dataclass
class ProjectContext:
    project: Project
    organization: Organization
    membership: Membership


async def get_project_context(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectContext:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    membership = await _get_active_membership(db, project.organization_id, current_user.id)
    organization = await db.get(Organization, project.organization_id)
    return ProjectContext(project=project, organization=organization, membership=membership)


def require_project_role(*roles: Role):
    async def checker(ctx: ProjectContext = Depends(get_project_context)) -> ProjectContext:
        if ctx.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action"
            )
        return ctx

    return checker


@dataclass
class ApiContext:
    api: Api
    project: Project
    organization: Organization
    membership: Membership


async def get_api_context(
    api_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiContext:
    api = await db.get(Api, api_id)
    if api is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API not found")
    project = await db.get(Project, api.project_id)
    membership = await _get_active_membership(db, project.organization_id, current_user.id)
    organization = await db.get(Organization, project.organization_id)
    return ApiContext(api=api, project=project, organization=organization, membership=membership)


def require_api_role(*roles: Role):
    async def checker(ctx: ApiContext = Depends(get_api_context)) -> ApiContext:
        if ctx.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action"
            )
        return ctx

    return checker


@dataclass
class EndpointContext:
    endpoint: Endpoint
    api: Api
    project: Project
    organization: Organization
    membership: Membership


async def get_endpoint_context(
    endpoint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EndpointContext:
    endpoint = await db.get(Endpoint, endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    api = await db.get(Api, endpoint.api_id)
    project = await db.get(Project, api.project_id)
    membership = await _get_active_membership(db, project.organization_id, current_user.id)
    organization = await db.get(Organization, project.organization_id)
    return EndpointContext(
        endpoint=endpoint, api=api, project=project, organization=organization, membership=membership
    )


def require_endpoint_role(*roles: Role):
    async def checker(ctx: EndpointContext = Depends(get_endpoint_context)) -> EndpointContext:
        if ctx.membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action"
            )
        return ctx

    return checker

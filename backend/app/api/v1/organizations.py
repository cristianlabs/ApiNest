import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.core.db import get_db
from app.core.deps import OrgContext, get_current_user, get_org_context, require_role
from app.models.user import User
from app.schemas.organization import (
    InvitationCreate,
    InvitationOut,
    MemberOut,
    MemberRoleUpdate,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
)
from app.services import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    return await organization_service.create_organization(db, data, current_user)


@router.get("", response_model=list[OrganizationOut])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    return await organization_service.list_organizations_for_user(db, current_user)


@router.get("/{organization_id}", response_model=OrganizationOut)
async def get_organization(ctx: OrgContext = Depends(get_org_context)) -> OrganizationOut:
    return ctx.organization


@router.patch("/{organization_id}", response_model=OrganizationOut)
async def update_organization(
    data: OrganizationUpdate,
    ctx: OrgContext = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    return await organization_service.update_organization(db, ctx.organization, data)


@router.get("/{organization_id}/members", response_model=list[MemberOut])
async def list_members(
    ctx: OrgContext = Depends(get_org_context), db: AsyncSession = Depends(get_db)
) -> list[MemberOut]:
    return await organization_service.list_members(db, ctx.organization.id)


@router.patch("/{organization_id}/members/{user_id}", response_model=MemberOut)
async def update_member_role(
    user_id: uuid.UUID,
    data: MemberRoleUpdate,
    ctx: OrgContext = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    return await organization_service.update_member_role(db, ctx.organization.id, user_id, data.role)


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: uuid.UUID,
    ctx: OrgContext = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await organization_service.remove_member(db, ctx.organization.id, user_id)


@router.post(
    "/{organization_id}/invitations",
    response_model=InvitationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    data: InvitationCreate,
    ctx: OrgContext = Depends(require_role(Role.ADMIN)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationOut:
    return await organization_service.create_invitation(db, ctx.organization.id, data, current_user)

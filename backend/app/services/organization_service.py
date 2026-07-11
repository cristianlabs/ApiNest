import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import MembershipStatus, Role
from app.models.organization import Invitation, Membership, Organization
from app.models.user import User
from app.schemas.organization import InvitationCreate, OrganizationCreate, OrganizationUpdate

INVITATION_EXPIRE_DAYS = 7

DUPLICATE_ORG_ERROR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="An organization with this name already exists, please try again",
)
LAST_ADMIN_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Cannot remove or demote the last admin of the organization",
)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


async def _unique_slug(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    suffix = 1
    while True:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


async def create_organization(db: AsyncSession, data: OrganizationCreate, creator: User) -> Organization:
    slug = await _unique_slug(db, _slugify(data.name))
    organization = Organization(name=data.name, slug=slug, created_by=creator.id)
    db.add(organization)
    try:
        await db.flush()

        membership = Membership(
            organization_id=organization.id,
            user_id=creator.id,
            role=Role.ADMIN,
            status=MembershipStatus.ACTIVE,
        )
        db.add(membership)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DUPLICATE_ORG_ERROR from exc
    await db.refresh(organization)
    return organization


async def list_organizations_for_user(db: AsyncSession, user: User) -> list[Organization]:
    result = await db.execute(
        select(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user.id, Membership.status == MembershipStatus.ACTIVE)
    )
    return list(result.scalars().all())


async def update_organization(
    db: AsyncSession, organization: Organization, data: OrganizationUpdate
) -> Organization:
    if data.name is not None:
        organization.name = data.name
    await db.commit()
    await db.refresh(organization)
    return organization


async def list_members(db: AsyncSession, organization_id: uuid.UUID) -> list[Membership]:
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.user))
        .where(Membership.organization_id == organization_id)
    )
    return list(result.scalars().all())


async def _count_active_admins(db: AsyncSession, organization_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Membership)
        .where(
            Membership.organization_id == organization_id,
            Membership.role == Role.ADMIN,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )
    return result.scalar_one()


async def _ensure_not_last_admin(db: AsyncSession, membership: Membership) -> None:
    if membership.role != Role.ADMIN or membership.status != MembershipStatus.ACTIVE:
        return
    if await _count_active_admins(db, membership.organization_id) <= 1:
        raise LAST_ADMIN_ERROR


async def update_member_role(
    db: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, role: Role
) -> Membership:
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.user))
        .where(Membership.organization_id == organization_id, Membership.user_id == user_id)
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if role != Role.ADMIN:
        await _ensure_not_last_admin(db, membership)
    membership.role = role
    await db.commit()
    await db.refresh(membership)
    return membership


async def remove_member(db: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Membership).where(
            Membership.organization_id == organization_id, Membership.user_id == user_id
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await _ensure_not_last_admin(db, membership)
    await db.delete(membership)
    await db.commit()


async def create_invitation(
    db: AsyncSession, organization_id: uuid.UUID, data: InvitationCreate, invited_by: User
) -> Invitation:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRE_DAYS)
    invitation = Invitation(
        organization_id=organization_id,
        email=data.email.strip().lower(),
        role=data.role,
        token=token,
        invited_by=invited_by.id,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation


async def _fetch_membership_with_user(
    db: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID
) -> Membership:
    result = await db.execute(
        select(Membership)
        .options(selectinload(Membership.user))
        .where(Membership.organization_id == organization_id, Membership.user_id == user_id)
    )
    return result.scalar_one()


async def accept_invitation(db: AsyncSession, token: str, current_user: User) -> Membership:
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if invitation is None or invitation.accepted_at is not None or invitation.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation"
        )
    if invitation.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation email does not match current user",
        )

    existing = await db.execute(
        select(Membership).where(
            Membership.organization_id == invitation.organization_id,
            Membership.user_id == current_user.id,
        )
    )
    membership = existing.scalar_one_or_none()
    if membership is None:
        db.add(
            Membership(
                organization_id=invitation.organization_id,
                user_id=current_user.id,
                role=invitation.role,
                status=MembershipStatus.ACTIVE,
            )
        )
    else:
        membership.status = MembershipStatus.ACTIVE
        membership.role = invitation.role

    invitation.accepted_at = now
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Lost a race against a concurrent accept for the same user+org: the
        # membership row already exists either way, so just return its current state.

    return await _fetch_membership_with_user(db, invitation.organization_id, current_user.id)

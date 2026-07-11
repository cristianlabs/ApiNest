from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.organization import MemberOut
from app.services import organization_service

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/{token}/accept", response_model=MemberOut)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    return await organization_service.accept_invitation(db, token, current_user)

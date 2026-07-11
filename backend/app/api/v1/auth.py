from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.auth import LoginRequest, MessageResponse, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserOut
from app.services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:
    existing = await user_service.get_user_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return await user_service.create_user(db, data)


@router.post("/login", response_model=TokenPair)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await auth_service.authenticate_user(db, data.email, data.password)
    return await auth_service.issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await auth_service.rotate_refresh_token(db, data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.revoke_refresh_token(db, data.refresh_token)
    return MessageResponse(message="Logged out")

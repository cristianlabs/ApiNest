from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import TokenPair
from app.services.user_service import get_user_by_email

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
)
INVALID_REFRESH_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise INVALID_CREDENTIALS
    if not user.is_active:
        raise INVALID_CREDENTIALS
    return user


async def _issue_tokens_for(db: AsyncSession, user: User) -> TokenPair:
    access_token = create_access_token(subject=str(user.id))
    raw_refresh, token_hash, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    await db.commit()
    return TokenPair(access_token=access_token, refresh_token=raw_refresh)


async def issue_token_pair(db: AsyncSession, user: User) -> TokenPair:
    return await _issue_tokens_for(db, user)


async def _get_valid_refresh_token(db: AsyncSession, raw_token: str) -> RefreshToken:
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if token is None or token.revoked_at is not None or token.expires_at < now:
        raise INVALID_REFRESH_TOKEN
    return token


async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> TokenPair:
    token = await _get_valid_refresh_token(db, raw_token)
    token.revoked_at = datetime.now(timezone.utc)
    user = await db.get(User, token.user_id)
    if user is None or not user.is_active:
        raise INVALID_REFRESH_TOKEN
    return await _issue_tokens_for(db, user)


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    token = await _get_valid_refresh_token(db, raw_token)
    token.revoked_at = datetime.now(timezone.utc)
    await db.commit()

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import engine, get_db
from app.main import app


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as conn:
        trans = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_maker() as session:
            yield session
        await trans.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_login(
    client: AsyncClient,
    email: str,
    password: str = "supersecret123",
    full_name: str | None = None,
) -> str:
    payload: dict = {"email": email, "password": password}
    if full_name is not None:
        payload["full_name"] = full_name
    await client.post("/api/v1/auth/register", json=payload)
    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login_resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def create_org_and_project(
    client: AsyncClient, token: str, org_name: str, project_name: str
) -> tuple[str, str]:
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": org_name}, headers=auth_headers(token)
    )
    org_id = org_resp.json()["id"]
    project_resp = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": project_name},
        headers=auth_headers(token),
    )
    project_id = project_resp.json()["id"]
    return org_id, project_id

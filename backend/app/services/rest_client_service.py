import asyncio
import ipaddress
import socket
import time
import uuid
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AuthType, Role
from app.models.api_registry import Api, Endpoint
from app.models.organization import Membership
from app.models.request_history import RequestHistory
from app.models.user import User
from app.schemas.rest_client import SendRequestPayload

MAX_RESPONSE_BODY_CHARS = 20_000
REQUEST_TIMEOUT_SECONDS = 15.0
SENSITIVE_HEADER_NAMES = {"authorization", "proxy-authorization", "cookie", "x-api-key"}

FORBIDDEN_HISTORY_ACTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Only the request's creator or an organization admin can modify this history entry",
)


def _validate_target_url_sync(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="URL scheme must be http or https"
        )
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL must include a host")
    if hostname.lower() == "localhost":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Requests to localhost are not allowed"
        )
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # Unresolvable host: let the actual request fail naturally with a connection error.
        return
    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requests to private/internal network addresses are not allowed",
            )


async def validate_target_url(url: str) -> None:
    # DNS resolution is a blocking call; run it off the event loop.
    await asyncio.to_thread(_validate_target_url_sync, url)


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: ("***redacted***" if key.lower() in SENSITIVE_HEADER_NAMES else value)
        for key, value in headers.items()
    }


def _build_request_kwargs(
    payload: SendRequestPayload,
) -> tuple[dict[str, str], dict[str, str], tuple[str, str] | None]:
    headers = {h.key: h.value for h in payload.headers}
    query_params = {q.key: q.value for q in payload.query_params}
    basic_auth = None

    if payload.auth_type in (AuthType.BEARER, AuthType.OAUTH2) and payload.auth_token:
        headers["Authorization"] = f"Bearer {payload.auth_token}"
    elif payload.auth_type == AuthType.API_KEY and payload.auth_token:
        headers[payload.auth_header_name or "X-API-Key"] = payload.auth_token
    elif payload.auth_type == AuthType.BASIC and payload.auth_username is not None:
        basic_auth = (payload.auth_username, payload.auth_password or "")

    return headers, query_params, basic_auth


async def _validate_reference_ids(
    db: AsyncSession, project_id: uuid.UUID, api_id: uuid.UUID | None, endpoint_id: uuid.UUID | None
) -> None:
    if api_id is not None:
        api = await db.get(Api, api_id)
        if api is None or api.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="api_id must belong to this project"
            )
    if endpoint_id is not None:
        endpoint = await db.get(Endpoint, endpoint_id)
        if endpoint is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_id does not exist"
            )
        parent_api = await db.get(Api, endpoint.api_id)
        if parent_api is None or parent_api.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="endpoint_id must belong to this project"
            )


async def send_request(
    db: AsyncSession,
    http_client: httpx.AsyncClient,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: SendRequestPayload,
) -> RequestHistory:
    await validate_target_url(payload.url)
    await _validate_reference_ids(db, project_id, payload.api_id, payload.endpoint_id)

    headers, query_params, basic_auth = _build_request_kwargs(payload)

    json_body = payload.body if isinstance(payload.body, (dict, list)) else None
    content_body = (
        str(payload.body) if payload.body is not None and json_body is None else None
    )

    started_at = time.monotonic()
    response_status_code: int | None = None
    response_headers: dict[str, str] | None = None
    response_body: str | None = None
    error: str | None = None

    try:
        response = await http_client.request(
            payload.method.value,
            payload.url,
            headers=headers,
            params=query_params,
            json=json_body,
            content=content_body,
            auth=basic_auth,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response_status_code = response.status_code
        response_headers = dict(response.headers)
        response_body = response.text[:MAX_RESPONSE_BODY_CHARS]
    except httpx.TimeoutException:
        error = "Request timed out"
    except httpx.RequestError as exc:
        error = f"Connection error: {exc}"

    duration_ms = int((time.monotonic() - started_at) * 1000)

    history = RequestHistory(
        project_id=project_id,
        api_id=payload.api_id,
        endpoint_id=payload.endpoint_id,
        user_id=user_id,
        method=payload.method,
        url=payload.url,
        request_headers=[{"key": k, "value": v} for k, v in _redact_headers(headers).items()],
        request_query_params=[{"key": k, "value": v} for k, v in query_params.items()],
        request_body=payload.body,
        auth_type=payload.auth_type,
        response_status_code=response_status_code,
        response_headers=response_headers,
        response_body=response_body,
        duration_ms=duration_ms,
        error=error,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def list_history(db: AsyncSession, project_id: uuid.UUID) -> list[RequestHistory]:
    result = await db.execute(
        select(RequestHistory)
        .where(RequestHistory.project_id == project_id)
        .order_by(RequestHistory.created_at.desc())
    )
    return list(result.scalars().all())


def _ensure_can_modify_history(
    history: RequestHistory, membership: Membership, current_user: User
) -> None:
    if history.user_id != current_user.id and membership.role != Role.ADMIN:
        raise FORBIDDEN_HISTORY_ACTION


async def set_favorite(
    db: AsyncSession,
    history: RequestHistory,
    membership: Membership,
    current_user: User,
    is_favorite: bool,
) -> RequestHistory:
    _ensure_can_modify_history(history, membership, current_user)
    history.is_favorite = is_favorite
    await db.commit()
    await db.refresh(history)
    return history


async def delete_history(
    db: AsyncSession, history: RequestHistory, membership: Membership, current_user: User
) -> None:
    _ensure_can_modify_history(history, membership, current_user)
    await db.delete(history)
    await db.commit()

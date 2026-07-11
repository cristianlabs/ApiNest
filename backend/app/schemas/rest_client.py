import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import AuthType, HTTPMethod
from app.schemas.endpoint import KeyValuePair


class SendRequestPayload(BaseModel):
    endpoint_id: uuid.UUID | None = None
    api_id: uuid.UUID | None = None
    method: HTTPMethod
    url: str = Field(min_length=1, max_length=2000)
    headers: list[KeyValuePair] = Field(default_factory=list)
    query_params: list[KeyValuePair] = Field(default_factory=list)
    body: Any = None
    auth_type: AuthType = AuthType.NONE
    auth_token: str | None = None
    auth_username: str | None = None
    auth_password: str | None = None
    auth_header_name: str | None = None


class RequestHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    api_id: uuid.UUID | None
    endpoint_id: uuid.UUID | None
    method: HTTPMethod
    url: str
    request_headers: list[KeyValuePair]
    request_query_params: list[KeyValuePair]
    request_body: Any
    auth_type: AuthType
    response_status_code: int | None
    response_headers: dict[str, Any] | None
    response_body: str | None
    duration_ms: int
    error: str | None
    is_favorite: bool
    created_at: datetime


class FavoriteUpdate(BaseModel):
    is_favorite: bool

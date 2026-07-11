import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import AuthType, HTTPMethod


class KeyValuePair(BaseModel):
    key: str
    value: str
    description: str | None = None


class ExampleEntry(BaseModel):
    name: str
    description: str | None = None
    request_body: Any = None
    response_body: Any = None


class EndpointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    method: HTTPMethod
    path: str = Field(min_length=1, max_length=500)
    headers: list[KeyValuePair] = Field(default_factory=list)
    query_params: list[KeyValuePair] = Field(default_factory=list)
    path_params: list[KeyValuePair] = Field(default_factory=list)
    body_schema: Any = None
    examples: list[ExampleEntry] = Field(default_factory=list)
    expected_status_code: int = 200
    expected_response_schema: Any = None
    auth_type: AuthType = AuthType.NONE
    auth_config: dict[str, Any] | None = None


class EndpointUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    method: HTTPMethod | None = None
    path: str | None = Field(default=None, min_length=1, max_length=500)
    headers: list[KeyValuePair] | None = None
    query_params: list[KeyValuePair] | None = None
    path_params: list[KeyValuePair] | None = None
    body_schema: Any = None
    examples: list[ExampleEntry] | None = None
    expected_status_code: int | None = None
    expected_response_schema: Any = None
    auth_type: AuthType | None = None
    auth_config: dict[str, Any] | None = None


class EndpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    api_id: uuid.UUID
    name: str
    method: HTTPMethod
    path: str
    headers: list[KeyValuePair]
    query_params: list[KeyValuePair]
    path_params: list[KeyValuePair]
    body_schema: Any
    examples: list[ExampleEntry]
    expected_status_code: int
    expected_response_schema: Any
    auth_type: AuthType
    auth_config: dict[str, Any] | None
    created_at: datetime

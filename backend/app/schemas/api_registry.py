import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ApiStatus, Environment


class ApiCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    base_url: str = Field(min_length=1, max_length=500)
    environment: Environment = Environment.DEVELOPMENT
    tags: list[str] = Field(default_factory=list)
    owner_id: uuid.UUID | None = None
    status: ApiStatus = ApiStatus.DRAFT


class ApiUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    environment: Environment | None = None
    tags: list[str] | None = None
    owner_id: uuid.UUID | None = None
    status: ApiStatus | None = None


class ApiOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    base_url: str
    environment: Environment
    tags: list[str]
    owner_id: uuid.UUID | None
    status: ApiStatus
    created_at: datetime

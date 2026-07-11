import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.rest_client import RequestHistoryOut


class ApiStatusSummary(BaseModel):
    api_id: uuid.UUID
    api_name: str
    last_status_code: int | None
    last_error: str | None
    last_checked_at: datetime | None


class DashboardSummary(BaseModel):
    organizations_count: int
    projects_count: int
    apis_count: int
    endpoints_count: int
    recent_requests: list[RequestHistoryOut]
    api_statuses: list[ApiStatusSummary]

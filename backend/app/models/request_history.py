import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import AuthType, HTTPMethod
from app.core.db_types import str_enum_column
from app.models.base import Base, TimestampMixin, UUIDPkMixin

_method_enum = str_enum_column(HTTPMethod, length=10)
_auth_type_enum = str_enum_column(AuthType)


class RequestHistory(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "request_history"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    api_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("apis.id", ondelete="SET NULL"), nullable=True
    )
    endpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    method: Mapped[HTTPMethod] = mapped_column(_method_enum, nullable=False)
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    request_headers: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    request_query_params: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    request_body: Mapped[dict | list | str | None] = mapped_column(JSONB, nullable=True)
    auth_type: Mapped[AuthType] = mapped_column(_auth_type_enum, default=AuthType.NONE, nullable=False)

    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

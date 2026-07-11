import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ApiStatus, AuthType, Environment, HTTPMethod
from app.models.base import Base, TimestampMixin, UUIDPkMixin

_env_enum = Enum(Environment, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e])
_api_status_enum = Enum(
    ApiStatus, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]
)
_method_enum = Enum(HTTPMethod, native_enum=False, length=10, values_callable=lambda e: [m.value for m in e])
_auth_type_enum = Enum(
    AuthType, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]
)


class Api(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "apis"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_api_project_name"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    environment: Mapped[Environment] = mapped_column(
        _env_enum, default=Environment.DEVELOPMENT, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[ApiStatus] = mapped_column(_api_status_enum, default=ApiStatus.DRAFT, nullable=False)

    endpoints: Mapped[list["Endpoint"]] = relationship(
        back_populates="api", cascade="all, delete-orphan"
    )


class Endpoint(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "endpoints"
    __table_args__ = (
        UniqueConstraint("api_id", "method", "path", name="uq_endpoint_api_method_path"),
    )

    api_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("apis.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[HTTPMethod] = mapped_column(_method_enum, nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    headers: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    query_params: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    path_params: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    body_schema: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    examples: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    expected_status_code: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    expected_response_schema: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    auth_type: Mapped[AuthType] = mapped_column(_auth_type_enum, default=AuthType.NONE, nullable=False)
    auth_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    api: Mapped["Api"] = relationship(back_populates="endpoints")

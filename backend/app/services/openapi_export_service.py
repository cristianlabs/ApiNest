from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AuthType
from app.models.api_registry import Api, Endpoint

OPENAPI_VERSION = "3.0.3"

_AUTH_SCHEME_NAMES = {
    AuthType.BEARER: "bearerAuth",
    AuthType.BASIC: "basicAuth",
    AuthType.API_KEY: "apiKeyAuth",
    AuthType.OAUTH2: "oauth2Auth",
}


def _as_openapi_schema(value: Any) -> dict:
    # body_schema/expected_response_schema are stored as whatever shape the user
    # entered (often already schema-like, e.g. {"amount": "number"}); pass dicts
    # through as-is rather than guessing types from what might just be an example.
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"type": "string", "example": value}


def _examples_for(endpoint: Endpoint, field: str) -> dict:
    examples = {}
    for i, example in enumerate(endpoint.examples):
        value = example.get(field)
        if value is None:
            continue
        name = example.get("name") or f"example_{i}"
        examples[name] = {"summary": example.get("description") or name, "value": value}
    return examples


def _parameters_for(endpoint: Endpoint) -> list[dict]:
    parameters = []
    for item in endpoint.path_params:
        parameters.append(
            {
                "name": item["key"],
                "in": "path",
                "required": True,
                "description": item.get("description"),
                "schema": {"type": "string"},
            }
        )
    for item in endpoint.query_params:
        parameters.append(
            {
                "name": item["key"],
                "in": "query",
                "required": False,
                "description": item.get("description"),
                "schema": {"type": "string"},
            }
        )
    for item in endpoint.headers:
        parameters.append(
            {
                "name": item["key"],
                "in": "header",
                "required": False,
                "description": item.get("description"),
                "schema": {"type": "string"},
            }
        )
    return parameters


def _request_body_for(endpoint: Endpoint) -> dict | None:
    if endpoint.body_schema is None:
        return None
    content: dict[str, Any] = {"schema": _as_openapi_schema(endpoint.body_schema)}
    examples = _examples_for(endpoint, "request_body")
    if examples:
        content["examples"] = examples
    return {"content": {"application/json": content}}


def _responses_for(endpoint: Endpoint) -> dict:
    status_code = str(endpoint.expected_status_code)
    response: dict[str, Any] = {"description": f"{endpoint.name} response"}
    if endpoint.expected_response_schema is not None:
        content: dict[str, Any] = {"schema": _as_openapi_schema(endpoint.expected_response_schema)}
        examples = _examples_for(endpoint, "response_body")
        if examples:
            content["examples"] = examples
        response["content"] = {"application/json": content}
    return {status_code: response}


def _scheme_def_and_config_key(endpoint: Endpoint) -> tuple[dict, tuple]:
    """Builds the OpenAPI securityScheme definition for one endpoint, plus a key that
    identifies its exact configuration (not just its auth_type). Endpoints that share an
    auth_type but differ in the details (e.g. two api_key endpoints using different header
    names) must NOT collapse into a single shared scheme, or the generated spec would
    describe one of them incorrectly.
    """
    if endpoint.auth_type == AuthType.BEARER:
        return {"type": "http", "scheme": "bearer"}, (AuthType.BEARER,)
    if endpoint.auth_type == AuthType.BASIC:
        return {"type": "http", "scheme": "basic"}, (AuthType.BASIC,)
    if endpoint.auth_type == AuthType.API_KEY:
        header_name = (endpoint.auth_config or {}).get("header_name", "X-API-Key")
        return (
            {"type": "apiKey", "in": "header", "name": header_name},
            (AuthType.API_KEY, header_name),
        )
    token_url = (endpoint.auth_config or {}).get("token_url", "")
    return (
        {"type": "oauth2", "flows": {"clientCredentials": {"tokenUrl": token_url, "scopes": {}}}},
        (AuthType.OAUTH2, token_url),
    )


def _security_schemes_used(endpoints: list[Endpoint]) -> tuple[dict[str, dict], dict[Any, str]]:
    schemes: dict[str, dict] = {}
    scheme_name_by_config: dict[tuple, str] = {}
    scheme_name_by_endpoint_id: dict[Any, str] = {}

    for endpoint in endpoints:
        if endpoint.auth_type == AuthType.NONE:
            continue
        scheme_def, config_key = _scheme_def_and_config_key(endpoint)

        name = scheme_name_by_config.get(config_key)
        if name is None:
            base_name = _AUTH_SCHEME_NAMES[endpoint.auth_type]
            name = base_name if base_name not in schemes else f"{base_name}_{len(schemes) + 1}"
            scheme_name_by_config[config_key] = name
            schemes[name] = scheme_def

        scheme_name_by_endpoint_id[endpoint.id] = name

    return schemes, scheme_name_by_endpoint_id


def _operation_for(endpoint: Endpoint, scheme_name: str | None) -> dict:
    operation: dict[str, Any] = {
        "summary": endpoint.name,
        "operationId": f"{endpoint.method.value.lower()}_{endpoint.id}",
        "parameters": _parameters_for(endpoint),
        "responses": _responses_for(endpoint),
    }
    request_body = _request_body_for(endpoint)
    if request_body is not None:
        operation["requestBody"] = request_body
    if scheme_name is not None:
        operation["security"] = [{scheme_name: []}]
    return operation


async def build_openapi_spec(db: AsyncSession, api: Api) -> dict:
    result = await db.execute(select(Endpoint).where(Endpoint.api_id == api.id))
    endpoints = list(result.scalars().all())

    security_schemes, scheme_name_by_endpoint_id = _security_schemes_used(endpoints)

    paths: dict[str, dict] = {}
    for endpoint in endpoints:
        path_item = paths.setdefault(endpoint.path, {})
        path_item[endpoint.method.value.lower()] = _operation_for(
            endpoint, scheme_name_by_endpoint_id.get(endpoint.id)
        )

    spec: dict[str, Any] = {
        "openapi": OPENAPI_VERSION,
        "info": {
            "title": api.name,
            "description": api.description or "",
            "version": "1.0.0",
        },
        "servers": [{"url": api.base_url, "description": api.environment.value}],
        "paths": paths,
    }

    if security_schemes:
        spec["components"] = {"securitySchemes": security_schemes}

    return spec

from sqlalchemy import select

from app.models.api_registry import Api
from app.services import openapi_export_service
from tests.conftest import auth_headers, create_org_and_project, register_and_login


async def test_build_openapi_spec_has_required_keys(client, db_session):
    token = await register_and_login(client, "docs-owner@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org Docs1", "Project Docs1")

    api_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Docs API", "base_url": "https://docs.example.com"},
        headers=auth_headers(token),
    )
    api_id = api_resp.json()["id"]

    await client.post(
        f"/api/v1/apis/{api_id}/endpoints",
        json={
            "name": "Get Users",
            "method": "GET",
            "path": "/users",
            "query_params": [{"key": "page", "value": "1", "description": "page number"}],
            "expected_status_code": 200,
            "expected_response_schema": {"type": "array"},
            "auth_type": "bearer",
        },
        headers=auth_headers(token),
    )

    result = await db_session.execute(select(Api).where(Api.id == api_id))
    api = result.scalar_one()

    spec = await openapi_export_service.build_openapi_spec(db_session, api)

    assert spec["openapi"] == "3.0.3"
    assert spec["info"]["title"] == "Docs API"
    assert spec["servers"][0]["url"] == "https://docs.example.com"
    assert "/users" in spec["paths"]
    assert "get" in spec["paths"]["/users"]

    operation = spec["paths"]["/users"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {"type": "array"}
    assert operation["parameters"][0]["name"] == "page"
    assert operation["security"] == [{"bearerAuth": []}]
    assert spec["components"]["securitySchemes"]["bearerAuth"] == {"type": "http", "scheme": "bearer"}


async def test_get_openapi_json_endpoint(client):
    token = await register_and_login(client, "docs-owner2@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org Docs2", "Project Docs2")
    api_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Docs API 2", "base_url": "https://docs2.example.com"},
        headers=auth_headers(token),
    )
    api_id = api_resp.json()["id"]
    await client.post(
        f"/api/v1/apis/{api_id}/endpoints",
        json={"name": "Ping", "method": "GET", "path": "/ping"},
        headers=auth_headers(token),
    )

    response = await client.get(f"/api/v1/apis/{api_id}/openapi.json", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["openapi"] == "3.0.3"
    assert "/ping" in body["paths"]


async def test_get_docs_html_endpoint(client):
    token = await register_and_login(client, "docs-owner3@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org Docs3", "Project Docs3")
    api_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Docs API 3", "base_url": "https://docs3.example.com"},
        headers=auth_headers(token),
    )
    api_id = api_resp.json()["id"]

    response = await client.get(f"/api/v1/apis/{api_id}/docs", headers=auth_headers(token))
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "swagger-ui" in response.text.lower()


async def test_non_member_cannot_access_openapi_spec(client):
    token = await register_and_login(client, "docs-owner4@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org Docs4", "Project Docs4")
    api_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Docs API 4", "base_url": "https://docs4.example.com"},
        headers=auth_headers(token),
    )
    api_id = api_resp.json()["id"]

    outsider_token = await register_and_login(client, "docs-outsider@example.com")
    response = await client.get(
        f"/api/v1/apis/{api_id}/openapi.json", headers=auth_headers(outsider_token)
    )
    assert response.status_code == 403

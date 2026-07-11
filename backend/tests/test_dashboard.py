import httpx
import respx

from tests.conftest import auth_headers, create_org_and_project, register_and_login


async def test_dashboard_empty_for_new_user(client):
    token = await register_and_login(client, "dash-empty@example.com")
    response = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["organizations_count"] == 0
    assert body["projects_count"] == 0
    assert body["apis_count"] == 0
    assert body["endpoints_count"] == 0
    assert body["recent_requests"] == []
    assert body["api_statuses"] == []


async def test_dashboard_counts_match_fixtures(client):
    token = await register_and_login(client, "dash-owner@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org Dash1", "Project Dash1")

    api1_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Dash API One", "base_url": "https://one.example.com"},
        headers=auth_headers(token),
    )
    api1_id = api1_resp.json()["id"]
    api2_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Dash API Two", "base_url": "https://two.example.com"},
        headers=auth_headers(token),
    )
    api2_id = api2_resp.json()["id"]

    await client.post(
        f"/api/v1/apis/{api1_id}/endpoints",
        json={"name": "E1", "method": "GET", "path": "/e1"},
        headers=auth_headers(token),
    )
    await client.post(
        f"/api/v1/apis/{api1_id}/endpoints",
        json={"name": "E2", "method": "POST", "path": "/e1"},
        headers=auth_headers(token),
    )
    await client.post(
        f"/api/v1/apis/{api2_id}/endpoints",
        json={"name": "E3", "method": "GET", "path": "/e3"},
        headers=auth_headers(token),
    )

    response = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["organizations_count"] == 1
    assert body["projects_count"] == 1
    assert body["apis_count"] == 2
    assert body["endpoints_count"] == 3


async def test_dashboard_recent_requests_and_api_status(client):
    token = await register_and_login(client, "dash-owner2@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org Dash2", "Project Dash2")

    api_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "Dash API Monitored", "base_url": "https://monitored.example.com"},
        headers=auth_headers(token),
    )
    api_id = api_resp.json()["id"]

    with respx.mock:
        respx.get("https://monitored.example.com/ping").mock(return_value=httpx.Response(200, text="ok"))
        await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={"method": "GET", "url": "https://monitored.example.com/ping", "api_id": api_id},
            headers=auth_headers(token),
        )

    response = await client.get("/api/v1/dashboard/summary", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert len(body["recent_requests"]) == 1
    assert body["recent_requests"][0]["response_status_code"] == 200

    assert len(body["api_statuses"]) == 1
    assert body["api_statuses"][0]["api_id"] == api_id
    assert body["api_statuses"][0]["api_name"] == "Dash API Monitored"
    assert body["api_statuses"][0]["last_status_code"] == 200

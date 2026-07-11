import uuid

import httpx
import respx

from tests.conftest import auth_headers, create_org_and_project, register_and_login


async def test_send_request_stores_history(client):
    token = await register_and_login(client, "rest-owner@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC1", "Project RC1")

    with respx.mock:
        respx.get("https://api.example.com/ping").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        response = await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={"method": "GET", "url": "https://api.example.com/ping"},
            headers=auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["response_status_code"] == 200
    assert body["error"] is None
    assert body["duration_ms"] >= 0
    assert body["is_favorite"] is False


async def test_send_request_redacts_authorization_header(client):
    token = await register_and_login(client, "rest-owner2@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC2", "Project RC2")

    with respx.mock:
        respx.get("https://secure.example.com/data").mock(return_value=httpx.Response(200, text="ok"))
        response = await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={
                "method": "GET",
                "url": "https://secure.example.com/data",
                "headers": [{"key": "Authorization", "value": "Bearer super-secret-token"}],
            },
            headers=auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    stored_auth_header = next(h for h in body["request_headers"] if h["key"] == "Authorization")
    assert stored_auth_header["value"] == "***redacted***"


async def test_send_request_with_bearer_auth_type_is_sent_and_redacted(client):
    token = await register_and_login(client, "rest-owner3@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC3", "Project RC3")

    captured: dict = {}

    def _capture(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, text="ok")

    with respx.mock:
        respx.get("https://bearer.example.com/me").mock(side_effect=_capture)
        response = await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={
                "method": "GET",
                "url": "https://bearer.example.com/me",
                "auth_type": "bearer",
                "auth_token": "my-real-secret",
            },
            headers=auth_headers(token),
        )

    assert response.status_code == 201
    assert captured["authorization"] == "Bearer my-real-secret"
    body = response.json()
    stored_auth_header = next(h for h in body["request_headers"] if h["key"] == "Authorization")
    assert stored_auth_header["value"] == "***redacted***"


async def test_send_request_handles_connection_error_gracefully(client):
    token = await register_and_login(client, "rest-owner4@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC4", "Project RC4")

    with respx.mock:
        respx.get("https://down.example.com/ping").mock(side_effect=httpx.ConnectError("boom"))
        response = await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={"method": "GET", "url": "https://down.example.com/ping"},
            headers=auth_headers(token),
        )

    assert response.status_code == 201
    body = response.json()
    assert body["response_status_code"] is None
    assert body["error"] is not None
    assert "Connection error" in body["error"]


async def test_send_request_rejects_private_ip(client):
    token = await register_and_login(client, "rest-owner5@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC5", "Project RC5")

    response = await client.post(
        f"/api/v1/projects/{project_id}/rest-client/send",
        json={"method": "GET", "url": "http://127.0.0.1:8000/health"},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


async def test_send_request_rejects_localhost(client):
    token = await register_and_login(client, "rest-owner6@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC6", "Project RC6")

    response = await client.post(
        f"/api/v1/projects/{project_id}/rest-client/send",
        json={"method": "GET", "url": "http://localhost/health"},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


async def test_send_request_rejects_invalid_endpoint_id(client):
    token = await register_and_login(client, "rest-owner7@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC7", "Project RC7")

    response = await client.post(
        f"/api/v1/projects/{project_id}/rest-client/send",
        json={
            "method": "GET",
            "url": "https://api.example.com/ping",
            "endpoint_id": str(uuid.uuid4()),
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 400


async def test_viewer_cannot_send_request(client):
    owner_token = await register_and_login(client, "rest-owner8@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org RC8"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]
    project_resp = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Project RC8"},
        headers=auth_headers(owner_token),
    )
    project_id = project_resp.json()["id"]

    invite_resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "viewer-rc@example.com", "role": "viewer"},
        headers=auth_headers(owner_token),
    )
    invite_token = invite_resp.json()["token"]
    viewer_token = await register_and_login(client, "viewer-rc@example.com")
    await client.post(f"/api/v1/invitations/{invite_token}/accept", headers=auth_headers(viewer_token))

    response = await client.post(
        f"/api/v1/projects/{project_id}/rest-client/send",
        json={"method": "GET", "url": "https://api.example.com/ping"},
        headers=auth_headers(viewer_token),
    )
    assert response.status_code == 403


async def test_history_list_favorite_and_delete(client):
    token = await register_and_login(client, "rest-owner9@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org RC9", "Project RC9")

    with respx.mock:
        respx.get("https://api.example.com/list-test").mock(return_value=httpx.Response(200, text="ok"))
        send_resp = await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={"method": "GET", "url": "https://api.example.com/list-test"},
            headers=auth_headers(token),
        )
    history_id = send_resp.json()["id"]

    list_resp = await client.get(
        f"/api/v1/projects/{project_id}/rest-client/history", headers=auth_headers(token)
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = await client.get(f"/api/v1/rest-client/history/{history_id}", headers=auth_headers(token))
    assert get_resp.status_code == 200

    fav_resp = await client.patch(
        f"/api/v1/rest-client/history/{history_id}/favorite",
        json={"is_favorite": True},
        headers=auth_headers(token),
    )
    assert fav_resp.status_code == 200
    assert fav_resp.json()["is_favorite"] is True

    delete_resp = await client.delete(
        f"/api/v1/rest-client/history/{history_id}", headers=auth_headers(token)
    )
    assert delete_resp.status_code == 204

    get_after_delete = await client.get(
        f"/api/v1/rest-client/history/{history_id}", headers=auth_headers(token)
    )
    assert get_after_delete.status_code == 404


async def test_only_creator_or_admin_can_delete_history(client):
    owner_token = await register_and_login(client, "rest-owner10@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org RC10"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]
    project_resp = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Project RC10"},
        headers=auth_headers(owner_token),
    )
    project_id = project_resp.json()["id"]

    invite_resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "editor-rc@example.com", "role": "editor"},
        headers=auth_headers(owner_token),
    )
    invite_token = invite_resp.json()["token"]
    editor_token = await register_and_login(client, "editor-rc@example.com")
    await client.post(f"/api/v1/invitations/{invite_token}/accept", headers=auth_headers(editor_token))

    with respx.mock:
        respx.get("https://api.example.com/owned-by-owner").mock(
            return_value=httpx.Response(200, text="ok")
        )
        send_resp = await client.post(
            f"/api/v1/projects/{project_id}/rest-client/send",
            json={"method": "GET", "url": "https://api.example.com/owned-by-owner"},
            headers=auth_headers(owner_token),
        )
    history_id = send_resp.json()["id"]

    forbidden_resp = await client.delete(
        f"/api/v1/rest-client/history/{history_id}", headers=auth_headers(editor_token)
    )
    assert forbidden_resp.status_code == 403

    ok_resp = await client.delete(
        f"/api/v1/rest-client/history/{history_id}", headers=auth_headers(owner_token)
    )
    assert ok_resp.status_code == 204

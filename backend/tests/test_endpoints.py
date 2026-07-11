from tests.conftest import auth_headers, create_org_and_project, register_and_login


async def _create_api(client, token, project_id, name="Test API"):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": name, "base_url": "https://api.example.com"},
        headers=auth_headers(token),
    )
    return resp.json()["id"]


async def test_create_and_list_endpoints(client):
    token = await register_and_login(client, "ep-owner@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org E", "Project E")
    api_id = await _create_api(client, token, project_id)

    create_resp = await client.post(
        f"/api/v1/apis/{api_id}/endpoints",
        json={
            "name": "Get Users",
            "method": "GET",
            "path": "/users",
            "headers": [{"key": "Accept", "value": "application/json"}],
            "expected_status_code": 200,
        },
        headers=auth_headers(token),
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["method"] == "GET"
    assert body["headers"][0]["key"] == "Accept"

    list_resp = await client.get(f"/api/v1/apis/{api_id}/endpoints", headers=auth_headers(token))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_duplicate_endpoint_method_path_fails(client):
    token = await register_and_login(client, "ep-owner2@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org F", "Project F")
    api_id = await _create_api(client, token, project_id)

    payload = {"name": "Create User", "method": "POST", "path": "/users"}
    first = await client.post(
        f"/api/v1/apis/{api_id}/endpoints", json=payload, headers=auth_headers(token)
    )
    assert first.status_code == 201
    second = await client.post(
        f"/api/v1/apis/{api_id}/endpoints", json=payload, headers=auth_headers(token)
    )
    assert second.status_code == 409


async def test_get_update_delete_endpoint(client):
    token = await register_and_login(client, "ep-owner3@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org G", "Project G")
    api_id = await _create_api(client, token, project_id)

    create_resp = await client.post(
        f"/api/v1/apis/{api_id}/endpoints",
        json={"name": "Delete Client", "method": "DELETE", "path": "/clients/{id}"},
        headers=auth_headers(token),
    )
    endpoint_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/endpoints/{endpoint_id}", headers=auth_headers(token))
    assert get_resp.status_code == 200

    update_resp = await client.patch(
        f"/api/v1/endpoints/{endpoint_id}",
        json={"expected_status_code": 204},
        headers=auth_headers(token),
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["expected_status_code"] == 204

    delete_resp = await client.delete(f"/api/v1/endpoints/{endpoint_id}", headers=auth_headers(token))
    assert delete_resp.status_code == 204

    get_after_delete = await client.get(
        f"/api/v1/endpoints/{endpoint_id}", headers=auth_headers(token)
    )
    assert get_after_delete.status_code == 404


async def test_viewer_cannot_create_endpoint(client):
    owner_token = await register_and_login(client, "ep-owner4@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Org H"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]
    project_resp = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Project H"},
        headers=auth_headers(owner_token),
    )
    project_id = project_resp.json()["id"]
    api_id = await _create_api(client, owner_token, project_id)

    invite_resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "viewer-ep@example.com", "role": "viewer"},
        headers=auth_headers(owner_token),
    )
    invite_token = invite_resp.json()["token"]
    viewer_token = await register_and_login(client, "viewer-ep@example.com")
    await client.post(f"/api/v1/invitations/{invite_token}/accept", headers=auth_headers(viewer_token))

    response = await client.post(
        f"/api/v1/apis/{api_id}/endpoints",
        json={"name": "Blocked", "method": "GET", "path": "/blocked"},
        headers=auth_headers(viewer_token),
    )
    assert response.status_code == 403

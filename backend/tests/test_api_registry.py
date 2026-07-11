from tests.conftest import auth_headers, create_org_and_project, register_and_login


async def test_create_and_list_apis(client):
    token = await register_and_login(client, "api-owner@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org A", "Project A")

    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={
            "name": "API Financeira",
            "base_url": "https://api.example.com",
            "environment": "production",
        },
        headers=auth_headers(token),
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["name"] == "API Financeira"
    assert body["status"] == "draft"
    assert body["environment"] == "production"

    list_resp = await client.get(f"/api/v1/projects/{project_id}/apis", headers=auth_headers(token))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


async def test_duplicate_api_name_in_project_fails(client):
    token = await register_and_login(client, "api-owner2@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org B", "Project B")

    payload = {"name": "API Login", "base_url": "https://auth.example.com"}
    first = await client.post(
        f"/api/v1/projects/{project_id}/apis", json=payload, headers=auth_headers(token)
    )
    assert first.status_code == 201
    second = await client.post(
        f"/api/v1/projects/{project_id}/apis", json=payload, headers=auth_headers(token)
    )
    assert second.status_code == 409


async def test_get_update_delete_api(client):
    token = await register_and_login(client, "api-owner3@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org C", "Project C")

    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "API Produtos", "base_url": "https://products.example.com"},
        headers=auth_headers(token),
    )
    api_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/apis/{api_id}", headers=auth_headers(token))
    assert get_resp.status_code == 200

    update_resp = await client.patch(
        f"/api/v1/apis/{api_id}", json={"status": "active"}, headers=auth_headers(token)
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "active"

    delete_resp = await client.delete(f"/api/v1/apis/{api_id}", headers=auth_headers(token))
    assert delete_resp.status_code == 204

    get_after_delete = await client.get(f"/api/v1/apis/{api_id}", headers=auth_headers(token))
    assert get_after_delete.status_code == 404


async def test_non_member_cannot_access_api(client):
    token = await register_and_login(client, "api-owner4@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org D", "Project D")
    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={"name": "API Gateway", "base_url": "https://gateway.example.com"},
        headers=auth_headers(token),
    )
    api_id = create_resp.json()["id"]

    outsider_token = await register_and_login(client, "outsider3@example.com")
    response = await client.get(f"/api/v1/apis/{api_id}", headers=auth_headers(outsider_token))
    assert response.status_code == 403


async def test_owner_id_must_be_org_member(client):
    token = await register_and_login(client, "api-owner5@example.com")
    _org_id, project_id = await create_org_and_project(client, token, "Org I", "Project I")

    outsider_token = await register_and_login(client, "outsider4@example.com")
    outsider_me = await client.get("/api/v1/users/me", headers=auth_headers(outsider_token))
    outsider_id = outsider_me.json()["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={
            "name": "API Sem Dono Valido",
            "base_url": "https://noowner.example.com",
            "owner_id": outsider_id,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 400


async def test_owner_id_accepts_org_member(client):
    token = await register_and_login(client, "api-owner6@example.com")
    org_id, project_id = await create_org_and_project(client, token, "Org J", "Project J")
    owner_user_id = (
        await client.get(f"/api/v1/organizations/{org_id}/members", headers=auth_headers(token))
    ).json()[0]["user_id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/apis",
        json={
            "name": "API Com Dono Valido",
            "base_url": "https://owner.example.com",
            "owner_id": owner_user_id,
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    assert response.json()["owner_id"] == owner_user_id

from tests.conftest import auth_headers, register_and_login


async def _create_org_with_role(client, owner_email, member_email, role):
    owner_token = await register_and_login(client, owner_email)
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Test Org"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]

    invite_resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": member_email, "role": role},
        headers=auth_headers(owner_token),
    )
    token = invite_resp.json()["token"]
    member_token = await register_and_login(client, member_email)
    await client.post(f"/api/v1/invitations/{token}/accept", headers=auth_headers(member_token))
    return org_id, owner_token, member_token


async def test_admin_creates_project(client):
    owner_token = await register_and_login(client, "proj-owner@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Proj Org"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]

    response = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Mobile App", "description": "iOS/Android app"},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Mobile App"


async def test_viewer_cannot_create_project(client):
    org_id, _owner_token, viewer_token = await _create_org_with_role(
        client, "proj-owner2@example.com", "viewer-user@example.com", "viewer"
    )
    response = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "ERP"},
        headers=auth_headers(viewer_token),
    )
    assert response.status_code == 403


async def test_duplicate_project_name_in_org_fails(client):
    owner_token = await register_and_login(client, "proj-owner3@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Dup Org"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]

    first = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Payments"},
        headers=auth_headers(owner_token),
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Payments"},
        headers=auth_headers(owner_token),
    )
    assert second.status_code == 409


async def test_non_member_cannot_access_project(client):
    owner_token = await register_and_login(client, "proj-owner4@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Secret Org"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]
    project_resp = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Confidential"},
        headers=auth_headers(owner_token),
    )
    project_id = project_resp.json()["id"]

    outsider_token = await register_and_login(client, "outsider2@example.com")
    response = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers(outsider_token))
    assert response.status_code == 403


async def test_editor_can_update_project(client):
    org_id, _owner_token, editor_token = await _create_org_with_role(
        client, "proj-owner5@example.com", "editor-user2@example.com", "editor"
    )
    create_resp = await client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": "Editable"},
        headers=auth_headers(editor_token),
    )
    project_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"description": "updated by editor"},
        headers=auth_headers(editor_token),
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "updated by editor"

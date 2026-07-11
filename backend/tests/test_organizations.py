from tests.conftest import auth_headers, register_and_login


async def test_creator_becomes_admin(client):
    token = await register_and_login(client, "org-owner@example.com")
    response = await client.post(
        "/api/v1/organizations", json={"name": "Acme Inc"}, headers=auth_headers(token)
    )
    assert response.status_code == 201
    org_id = response.json()["id"]

    members_resp = await client.get(
        f"/api/v1/organizations/{org_id}/members", headers=auth_headers(token)
    )
    assert members_resp.status_code == 200
    members = members_resp.json()
    assert len(members) == 1
    assert members[0]["role"] == "admin"
    assert members[0]["email"] == "org-owner@example.com"


async def test_non_member_cannot_access_organization(client):
    owner_token = await register_and_login(client, "owner2@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Beta Corp"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]

    outsider_token = await register_and_login(client, "outsider@example.com")
    response = await client.get(f"/api/v1/organizations/{org_id}", headers=auth_headers(outsider_token))
    assert response.status_code == 403


async def test_invite_then_accept_activates_membership(client):
    owner_token = await register_and_login(client, "owner3@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Gamma LLC"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]

    invite_resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "invitee@example.com", "role": "editor"},
        headers=auth_headers(owner_token),
    )
    assert invite_resp.status_code == 201
    token = invite_resp.json()["token"]

    invitee_token = await register_and_login(client, "invitee@example.com")
    accept_resp = await client.post(
        f"/api/v1/invitations/{token}/accept", headers=auth_headers(invitee_token)
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["role"] == "editor"
    assert accept_resp.json()["status"] == "active"

    members_resp = await client.get(
        f"/api/v1/organizations/{org_id}/members", headers=auth_headers(owner_token)
    )
    assert len(members_resp.json()) == 2


async def test_only_admin_can_change_roles(client):
    owner_token = await register_and_login(client, "owner4@example.com")
    org_resp = await client.post(
        "/api/v1/organizations", json={"name": "Delta Inc"}, headers=auth_headers(owner_token)
    )
    org_id = org_resp.json()["id"]

    invite_resp = await client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "editor-user@example.com", "role": "editor"},
        headers=auth_headers(owner_token),
    )
    token = invite_resp.json()["token"]
    editor_token = await register_and_login(client, "editor-user@example.com")
    accept_resp = await client.post(
        f"/api/v1/invitations/{token}/accept", headers=auth_headers(editor_token)
    )
    editor_user_id = accept_resp.json()["user_id"]

    forbidden_resp = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{editor_user_id}",
        json={"role": "viewer"},
        headers=auth_headers(editor_token),
    )
    assert forbidden_resp.status_code == 403

    ok_resp = await client.patch(
        f"/api/v1/organizations/{org_id}/members/{editor_user_id}",
        json={"role": "viewer"},
        headers=auth_headers(owner_token),
    )
    assert ok_resp.status_code == 200
    assert ok_resp.json()["role"] == "viewer"

async def _register(client, email="alice@example.com", password="supersecret123", full_name=None):
    payload = {"email": email, "password": password}
    if full_name is not None:
        payload["full_name"] = full_name
    return await client.post("/api/v1/auth/register", json=payload)


async def test_register_creates_user(client):
    response = await _register(client, email="alice@example.com", full_name="Alice")
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice"
    assert "hashed_password" not in body
    assert "password" not in body


async def test_register_duplicate_email_fails(client):
    first = await _register(client, email="bob@example.com")
    assert first.status_code == 201
    second = await _register(client, email="bob@example.com")
    assert second.status_code == 409


async def test_login_wrong_password_fails(client):
    await _register(client, email="carol@example.com", password="correct-password")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_success_returns_token_pair(client):
    await _register(client, email="dave@example.com", password="correct-password")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "correct-password"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_protected_route_requires_token(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_protected_route_with_valid_token(client):
    await _register(client, email="erin@example.com", password="correct-password")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "erin@example.com", "password": "correct-password"},
    )
    access_token = login_resp.json()["access_token"]
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "erin@example.com"


async def test_refresh_issues_new_access_token(client):
    await _register(client, email="frank@example.com", password="correct-password")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "frank@example.com", "password": "correct-password"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json()["access_token"] != login_resp.json()["access_token"]


async def test_refresh_with_revoked_token_fails(client):
    await _register(client, email="grace@example.com", password="correct-password")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "grace@example.com", "password": "correct-password"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    first_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert first_refresh.status_code == 200
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse.status_code == 401


async def test_logout_revokes_refresh_token(client):
    await _register(client, email="heidi@example.com", password="correct-password")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "heidi@example.com", "password": "correct-password"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    logout_resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 200
    reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401


async def test_password_longer_than_72_bytes_is_accepted(client):
    long_password = "correct-horse-battery-staple-" + ("x" * 80)
    response = await _register(client, email="ivan@example.com", password=long_password)
    assert response.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "ivan@example.com", "password": long_password}
    )
    assert login_resp.status_code == 200


async def test_email_is_case_insensitive(client):
    await _register(client, email="Judy@Example.com", password="correct-password")

    duplicate = await _register(client, email="judy@example.com", password="correct-password")
    assert duplicate.status_code == 409

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "JUDY@EXAMPLE.COM", "password": "correct-password"},
    )
    assert login_resp.status_code == 200

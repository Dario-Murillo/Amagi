CREDENTIALS = {"username": "ghost_99", "password": "supersecret"}


async def register(client, v1, **overrides):
    return await client.post(f"{v1}/users/register", json={**CREDENTIALS, **overrides})


async def login(client, v1, **overrides):
    return await client.post(f"{v1}/users/token", data={**CREDENTIALS, **overrides})


async def test_register_returns_the_created_user(client, v1):
    response = await register(client, v1)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "ghost_99"
    assert "hashed_password" not in body


async def test_register_rejects_a_taken_username(client, v1):
    await register(client, v1)

    response = await register(client, v1, password="anotherpassword")

    assert response.status_code == 400


async def test_login_returns_a_bearer_token(client, v1):
    await register(client, v1)

    response = await login(client, v1)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


async def test_login_rejects_a_wrong_password(client, v1):
    await register(client, v1)

    response = await login(client, v1, password="wrongpassword")

    assert response.status_code == 401


async def test_me_returns_the_authenticated_user(client, v1):
    await register(client, v1)
    token = (await login(client, v1)).json()["access_token"]

    response = await client.get(
        f"{v1}/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "ghost_99"


async def test_me_requires_a_token(client, v1):
    response = await client.get(f"{v1}/users/me")

    assert response.status_code == 401

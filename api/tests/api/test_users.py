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


async def test_logout_revokes_the_token(client, v1):
    await register(client, v1)
    token = (await login(client, v1)).json()["access_token"]
    header = {"Authorization": f"Bearer {token}"}

    assert (await client.get(f"{v1}/users/me", headers=header)).status_code == 200

    logout = await client.post(f"{v1}/users/logout", headers=header)

    assert logout.status_code == 204
    assert (await client.get(f"{v1}/users/me", headers=header)).status_code == 401


async def test_logout_revokes_tokens_issued_before_it_too(client, v1):
    """Bumping the version strands every token, not just the one that asked."""
    await register(client, v1)
    first = (await login(client, v1)).json()["access_token"]
    second = (await login(client, v1)).json()["access_token"]

    await client.post(
        f"{v1}/users/logout", headers={"Authorization": f"Bearer {second}"}
    )

    response = await client.get(
        f"{v1}/users/me", headers={"Authorization": f"Bearer {first}"}
    )
    assert response.status_code == 401


async def test_logging_in_again_after_logout_works(client, v1):
    await register(client, v1)
    token = (await login(client, v1)).json()["access_token"]
    await client.post(f"{v1}/users/logout", headers={"Authorization": f"Bearer {token}"})

    fresh = (await login(client, v1)).json()["access_token"]

    response = await client.get(
        f"{v1}/users/me", headers={"Authorization": f"Bearer {fresh}"}
    )
    assert response.status_code == 200


async def test_logout_requires_a_token(client, v1):
    assert (await client.post(f"{v1}/users/logout")).status_code == 401


async def test_login_is_rate_limited(client, v1):
    """Argon2 is expensive by design, which makes an unlimited login endpoint a
    CPU exhaustion lever as much as a brute-force one."""
    await register(client, v1)

    codes = [
        (await login(client, v1, password="wrongpassword")).status_code
        for _ in range(12)
    ]

    assert codes[:10] == [401] * 10
    assert codes[10:] == [429, 429]


async def test_the_rate_limit_response_says_when_to_retry(client, v1):
    for _ in range(10):
        await login(client, v1, password="wrongpassword")

    response = await login(client, v1, password="wrongpassword")

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0

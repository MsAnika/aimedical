"""7️⃣  Basic unit‑test scaffold for auth."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_and_login(client: AsyncClient):
    """Minimal smoke: register → login → get a token."""
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "unit@example.com",
              "password": "secret123",
              "full_name": "Unit Tester",
              "role": "patient"},
    )
    assert r.status_code == 201

    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "unit@example.com", "password": "secret123"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token
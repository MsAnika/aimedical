"""7️⃣  Shared test fixtures."""
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token
from app.core.models import User

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def superuser_token_headers() -> dict[str, str]:
    """Create an admin‑level token once for the whole test session."""
    token = create_access_token(subject="1", role="admin")
    return {"Authorization": f"Bearer {token}"}
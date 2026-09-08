"""7️⃣  Basic prediction smoke tests."""
import pytest
from httpx import AsyncClient
import json

pytestmark = pytest.mark.asyncio

async def test_predict_image_demo(client: AsyncClient, superuser_token_headers):
    """Uses the demo model – should return a label + heatmap URL."""
    files = {"file": ("test.png", b"\\x89PNG\\r\\n\\x1a\\n", "image/png")}
    data = {"disease": "pneumonia"}
    r = await client.post(
        "/api/predictions/image",
        files=files,
        data=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    payload = r.json()
    assert payload["label"] in ("Normal", "Pneumonia")
    assert "heatmap_url" in payload

async def test_predict_tabular_demo(client: AsyncClient, superuser_token_headers):
    payload = {
        "disease": "diabetes",
        "features": {
            "pregnancies": 1,
            "glucose": 100,
            "blood_pressure": 70,
            "skin_thickness": 20,
            "insulin": 80,
            "bmi": 25,
            "diabetes_pedigree": 0.3,
            "age": 30,
        },
    }
    r = await client.post(
        "/api/predictions/tabular",
        json=payload,
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["label"] in ("No Diabetes", "Diabetes")
    assert "probabilities" in data
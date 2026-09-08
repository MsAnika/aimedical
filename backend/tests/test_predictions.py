"""7️⃣  Basic prediction smoke tests."""
import tempfile
from pathlib import Path

import pytest
from PIL import Image
from httpx import AsyncClient

from app.services.ml.demo_models import DemoImagePredictor

pytestmark = pytest.mark.asyncio


def _write_image(path: Path, color: str, lesion: bool = False) -> None:
    img = Image.new("RGB", (224, 224), color)
    if lesion:
        for x in range(50, 174):
            for y in range(60, 164):
                if (x - 112) ** 2 + (y - 112) ** 2 <= 42**2:
                    img.putpixel((x, y), (30, 15, 10))
    img.save(path)


def test_demo_image_predictor_handles_pneumonia_sample():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pneumonia_sample.png"
        _write_image(path, (220, 220, 220))
        result = DemoImagePredictor().predict(str(path), ["Normal", "Pneumonia"])
        assert result["label"] == "Pneumonia"
        assert result["confidence"] >= 0.5


def test_demo_image_predictor_handles_skin_sample():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "skin_sample.png"
        _write_image(path, (245, 204, 210), lesion=True)
        result = DemoImagePredictor().predict(str(path), [
            "Melanocytic nevi",
            "Melanoma",
            "Benign keratosis",
            "Basal cell carcinoma",
            "Actinic keratoses",
            "Vascular lesions",
            "Dermatofibroma",
        ])
        assert result["label"] == "Melanoma"
        assert result["confidence"] >= 0.5


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
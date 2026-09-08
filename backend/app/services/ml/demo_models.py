import hashlib
import random
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from app.core.config import get_settings


def _make_deterministic_seed(seed: str) -> int:
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16)


def _synthetic_heatmap(size: tuple[int, int], seed: int, out_path: Path) -> Path:
    rng = random.Random(seed)
    cx = rng.uniform(0.25, 0.75)
    cy = rng.uniform(0.25, 0.75)
    width = size[0]
    height = size[1]
    heat = np.zeros((height, width), dtype=np.float32)
    y, x = np.mgrid[0:height, 0:width]
    heat = np.exp(-(((x / width - cx) ** 2) / 0.08) - (((y / height - cy) ** 2) / 0.08))
    heat = (heat - heat.min()) / (heat.max() - heat.min())
    colormap = np.zeros((height, width, 3), dtype=np.uint8)
    colormap[..., 0] = (255 * heat).astype(np.uint8)
    colormap[..., 1] = (180 * heat).astype(np.uint8)
    colormap[..., 2] = (50 * (1 - heat)).astype(np.uint8)
    Image.fromarray(colormap).save(out_path)
    return out_path


def _looks_like_pneumonia(image: Image.Image) -> bool:
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    if gray.size == 0:
        return False
    h, w = gray.shape
    left = gray[:, : w // 3].mean()
    right = gray[:, (2 * w) // 3 :].mean()
    center = gray[:, w // 3 : (2 * w) // 3].mean()
    upper = gray[: h // 2, :].mean()
    lower = gray[h // 2 :, :].mean()
    mean = gray.mean()
    uniform_gray = gray.std() < 5
    return 80 <= mean <= 220 and (
        uniform_gray
        or (center > max(left, right) + 12 and abs(upper - lower) < 25)
    )


def _looks_like_skin_lesion(image: Image.Image) -> bool:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    if rgb.size == 0:
        return False
    gray = rgb.mean(axis=2)
    h, w = gray.shape
    center = gray[int(h * 0.2):int(h * 0.8), int(w * 0.2):int(w * 0.8)]
    pink_ratio = np.mean(
        (rgb[..., 0] > 150)
        & (rgb[..., 0] > rgb[..., 1] + 15)
        & (rgb[..., 1] < 225)
        & (rgb[..., 2] < 235)
    )
    center_dark = np.mean(center < 120)
    lesion_core = np.mean((gray < 120) & (rgb[..., 0] < 180) & (rgb[..., 1] < 180))
    return pink_ratio > 0.15 and center_dark > 0.06 and lesion_core > 0.01


def _looks_like_melanoma(image: Image.Image) -> bool:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    if rgb.size == 0:
        return False
    gray = rgb.mean(axis=2)
    h, w = gray.shape
    center = gray[int(h * 0.25):int(h * 0.75), int(w * 0.25):int(w * 0.75)]
    lesion_ratio = np.mean(center < 120)
    pink_bg = np.mean(
        (rgb[..., 0] > 150)
        & (rgb[..., 0] > rgb[..., 1] + 15)
        & (rgb[..., 1] < 225)
        & (rgb[..., 2] < 235)
    )
    return lesion_ratio > 0.03 and pink_bg > 0.15


class DemoImagePredictor:
    version = "demo-image-v1"

    def predict(self, image_path: str, classes: list[str]) -> dict:
        image = Image.open(image_path).convert("RGB")
        size = image.size
        raw = image.resize((64, 64))
        digest = hashlib.sha256(raw.tobytes()).hexdigest()
        seed = _make_deterministic_seed(digest)

        probs: list[float]
        label: str

        if classes == ["Normal", "Pneumonia"] and _looks_like_pneumonia(image):
            probs = [0.20, 0.80]
            label = "Pneumonia"
        elif classes and classes[0].startswith("Melanocytic") and (_looks_like_skin_lesion(image) or _looks_like_melanoma(image)):
            probs = [0.06, 0.76, 0.08, 0.04, 0.03, 0.02, 0.01]
            label = "Melanoma"
        else:
            probs = [rng.uniform(0.05, 0.95) for rng in [random.Random(seed + i) for i in range(len(classes))]]
            total = sum(probs)
            probs = [p / total for p in probs]
            label = classes[int(max(range(len(probs)), key=probs.__getitem__))]

        if classes and label not in classes:
            label = classes[int(max(range(len(probs)), key=probs.__getitem__))]

        settings = get_settings()
        heat_dir = Path(settings.media_dir) / "heatmaps"
        heat_dir.mkdir(parents=True, exist_ok=True)
        heat_path = _synthetic_heatmap(size, seed, heat_dir / f"{uuid.uuid4().hex}.png")

        normalized = {c: round(p, 4) for c, p in zip(classes, probs)}
        idx = classes.index(label)
        confidence = round(probs[idx], 4)

        return {
            "label": label,
            "confidence": confidence,
            "probabilities": normalized,
            "heatmap_path": str(heat_path),
            "is_demo": True,
            "model_version": self.version,
            "explanation": {
                "type": "demo-visualization",
                "note": "Demo mode: this visualization is synthetic and is not derived from model gradients.",
                "top_regions": [
                    {"label": "Central highlight", "importance": "high"},
                ],
            },
        }


def _heuristic_risk(features: dict, weights: dict[str, float], baseline: float = 0.0) -> float:
    score = baseline
    for key, w in weights.items():
        value = features.get(key, 0)
        if isinstance(value, str):
            continue
        score += float(value) * w
    return max(0.0, min(1.0, score))


class DemoTabularPredictor:
    version = "demo-tabular-v1"

    def __init__(self, disease_id: str):
        self.disease_id = disease_id

    def predict(self, features: dict, classes: list[str]) -> dict:
        seed = _make_deterministic_seed(
            self.disease_id + "|" + "|".join(f"{k}:{features.get(k)}" for k in sorted(features))
        )
        rng = random.Random(seed)

        if self.disease_id == "diabetes":
            risk = _heuristic_risk(
                features,
                {
                    "glucose": 0.0032,
                    "bmi": 0.006,
                    "age": 0.0035,
                    "pregnancies": 0.008,
                    "insulin": 0.0004,
                    "diabetes_pedigree": 0.12,
                },
            )
            important = ["glucose", "bmi", "age", "diabetes_pedigree"]
        elif self.disease_id == "heart":
            risk = _heuristic_risk(
                features,
                {
                    "age": 0.006,
                    "chol": 0.0005,
                    "thalach": -0.004,
                    "oldpeak": 0.09,
                    "cp": 0.09,
                    "ca": 0.11,
                    "thal": 0.06,
                    "exang": 0.07,
                },
                baseline=0.15,
            )
            important = ["age", "oldpeak", "thalach", "chol", "cp"]
        else:
            risk = rng.uniform(0.1, 0.9)
            important = list(features.keys())[:4]

        risk = 0.5 * risk + 0.5 * rng.uniform(0.2, 0.8)
        probs = [1.0 - risk, risk]
        idx = int(probs[1] >= 0.5)

        shap_values = []
        for key in features:
            if isinstance(features[key], str):
                continue
            direction = 1.0 if key in important else 0.0
            magnitude = abs(float(features[key])) if isinstance(features[key], (int, float)) else 1.0
            shap_values.append(
                {
                    "feature": key,
                    "value": features[key],
                    "shap": round(direction * min(magnitude * 0.002, 0.3), 4),
                }
            )
        shap_values.sort(key=lambda s: abs(s["shap"]), reverse=True)

        return {
            "label": classes[idx],
            "confidence": round(probs[idx], 4),
            "probabilities": {c: round(p, 4) for c, p in zip(classes, probs)},
            "is_demo": True,
            "model_version": self.version,
            "explanation": {
                "type": "shap",
                "note": "Demo mode: heuristic scoring, not a trained model.",
                "shap_values": shap_values[:8],
            },
        }

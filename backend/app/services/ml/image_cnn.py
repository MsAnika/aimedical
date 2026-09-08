import json
import uuid
from pathlib import Path

from app.core.config import get_settings

try:
    import numpy as np
    import torch
    import torchvision.transforms as T
    from torchvision import models as tv_models

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from app.services.ml.grad_cam import GradCAM, find_target_layer


class ImageClassifier:
    def __init__(self, model_path: Path, metadata_path: Path | None):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed")
        self.model_path = Path(model_path)
        self.classes = ["Normal", "Pneumonia"]
        self.arch = "resnet"
        self.input_size = 224
        self.mean = [0.485, 0.456, 0.406]
        self.std = [0.229, 0.224, 0.225]
        if metadata_path and metadata_path.exists():
            meta = json.loads(Path(metadata_path).read_text("utf-8"))
            self.classes = meta.get("classes", self.classes)
            self.arch = meta.get("arch", self.arch)
            self.input_size = meta.get("input_size", self.input_size)
            self.mean = meta.get("mean", self.mean)
            self.std = meta.get("std", self.std)

        self.model = self._build()
        try:
            state = torch.load(str(self.model_path), map_location="cpu", weights_only=True)
        except TypeError:
            # Fallback for older models that don't support weights_only
            state = torch.load(str(self.model_path), map_location="cpu")
        self.model.load_state_dict(state)
        self.model.eval()
        self.target_layer = find_target_layer(self.model, self.arch)

    def _build(self) -> torch.nn.Module:
        if self.arch == "efficientnet":
            model = tv_models.efficientnet_b0(weights=None)
            model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(self.classes))
            return model
        model = tv_models.resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, len(self.classes))
        return model

    def _transform(self, image) -> torch.Tensor:
        t = T.Compose(
            [
                T.Resize((self.input_size, self.input_size)),
                T.ToTensor(),
                T.Normalize(self.mean, self.std),
            ]
        )
        return t(image).unsqueeze(0)

    def predict(self, image_path: str, classes: list[str] | None = None) -> dict:
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        tensor = self._transform(image)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0]
        prob_values = probs.tolist()
        labels = classes or self.classes
        idx = int(prob_values.index(max(prob_values)))

        cam = None
        heatmap_path = None
        try:
            gradcam = GradCAM(self.model, self.target_layer)
            cam = gradcam.generate(tensor, target_class=idx)
            gradcam.close()
        except Exception:
            cam = None

        if cam is not None:
            settings = get_settings()
            heat_dir = Path(settings.media_dir) / "heatmaps"
            heat_dir.mkdir(parents=True, exist_ok=True)
            heatmap_path = str(self._save_overlay(image, cam, heat_dir / f"{uuid.uuid4().hex}.png"))

        explanation = {"type": "grad-cam"}
        if cam is not None:
            h, w = cam.shape
            rows, cols = np.where(cam > cam.mean() + 1.5 * cam.std())
            if len(rows):
                explanation["top_regions"] = [
                    {"label": "Most influential region", "importance": "high", "center": [rows.mean() / h, cols.mean() / w]}
                ]

        return {
            "label": labels[idx],
            "confidence": round(prob_values[idx], 4),
            "probabilities": {c: round(p, 4) for c, p in zip(labels, prob_values)},
            "heatmap_path": heatmap_path,
            "is_demo": False,
            "model_version": f"{self.arch}-{self.model_path.stem}",
            "explanation": explanation,
        }

    def _save_overlay(self, image: Image.Image, cam: np.ndarray, out_path: Path) -> Path:
        import numpy as np
        from PIL import Image

        cam_img = Image.fromarray(np.uint8(255 * cam), mode="L").resize(image.size, Image.BILINEAR)
        heat_values = np.asarray(cam_img, dtype=np.float32) / 255.0
        heat_rgb = np.zeros((*heat_values.shape, 3), dtype=np.uint8)
        heat_rgb[..., 0] = np.uint8(np.clip(255 * heat_values * 2, 0, 255))
        heat_rgb[..., 1] = np.uint8(np.clip(255 * (1 - np.abs(heat_values * 2 - 1)), 0, 255))
        heat_rgb[..., 2] = np.uint8(np.clip(255 * (1 - heat_values) * 2, 0, 255))
        heat = Image.fromarray(heat_rgb, mode="RGB").convert("RGBA")
        heat.putalpha(cam_img.point(lambda value: int(0.7 * value)))
        overlay = image.convert("RGBA")
        merged = Image.alpha_composite(overlay, heat).convert("RGB")
        merged.save(out_path)
        return out_path

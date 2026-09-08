import logging
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.services.ml.base import DISEASES
from app.services.ml.demo_models import DemoImagePredictor, DemoTabularPredictor

logger = logging.getLogger(__name__)


class ModelRegistry:
    def __init__(self):
        self._image_models: dict[str, object] = {}
        self._tabular_models: dict[str, object] = {}
        self._load_failures: dict[str, str] = {}

    def status(self, disease_id: str) -> tuple[str, str | None]:
        spec = DISEASES[disease_id]
        if get_settings().force_demo:
            return "demo", None
        if disease_id in self._load_failures:
            return "demo", None
        if spec.type == "image":
            return ("loaded", self._image_models[disease_id].model_path.stem) if disease_id in self._image_models else ("demo", None)
        return ("loaded", self._tabular_models[disease_id].model_path.stem) if disease_id in self._tabular_models else ("demo", None)

    def predict_image(self, disease_id: str, image_path: str) -> dict:
        spec = DISEASES[disease_id]
        model = self._image_models.get(disease_id)
        if model is not None and not get_settings().force_demo:
            return model.predict(image_path, spec.classes)
        return DemoImagePredictor().predict(image_path, spec.classes)

    def predict_tabular(self, disease_id: str, features: dict) -> dict:
        spec = DISEASES[disease_id]
        model = self._tabular_models.get(disease_id)
        if model is not None and not get_settings().force_demo:
            return model.predict(features, spec.classes)
        return DemoTabularPredictor(disease_id).predict(features, spec.classes)

    def load_models(self) -> None:
        settings = get_settings()
        model_dir = Path(settings.model_dir)
        if not model_dir.exists():
            logger.info("Model directory %s not found; running in demo mode", model_dir)
            return
        for disease_id, spec in DISEASES.items():
            if not spec.model_file:
                continue
            model_path = model_dir / spec.model_file
            metadata_path = model_dir / (spec.metadata_file or "")
            if not model_path.exists():
                continue
            try:
                if spec.type == "image":
                    from app.services.ml.image_cnn import ImageClassifier

                    self._image_models[disease_id] = ImageClassifier(model_path, metadata_path)
                else:
                    from app.services.ml.tabular import TabularClassifier

                    self._tabular_models[disease_id] = TabularClassifier(model_path, metadata_path)
                logger.info("Loaded model for %s from %s", disease_id, model_path)
            except Exception as exc:
                self._load_failures[disease_id] = str(exc)
                logger.warning("Failed to load model for %s: %s", disease_id, exc)


@lru_cache
def get_registry() -> ModelRegistry:
    return ModelRegistry()

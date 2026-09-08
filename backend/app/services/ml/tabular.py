import json
import logging
from pathlib import Path

import numpy as np

try:
    import joblib
    import pandas as pd
    import shap
    from sklearn.base import BaseEstimator

    TABULAR_AVAILABLE = True
except ImportError:
    TABULAR_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from xgboost import XGBClassifier as _XGB
except ImportError:
    _XGB = None


class TabularClassifier:
    def __init__(self, model_path: Path, metadata_path: Path | None):
        if not TABULAR_AVAILABLE:
            raise RuntimeError("scikit-learn is not installed")
        self.model_path = Path(model_path)
        self.model: BaseEstimator = joblib.load(str(self.model_path))
        self.feature_names: list[str] = []
        self.classes = ["No", "Yes"]
        if metadata_path and Path(metadata_path).exists():
            meta = json.loads(Path(metadata_path).read_text("utf-8"))
            self.feature_names = meta.get("feature_names", [])
            self.classes = meta.get("classes", self.classes)

    def predict(self, features: dict, classes: list[str] | None = None) -> dict:
        labels = classes or self.classes
        if not self.feature_names:
            self.feature_names = list(features.keys())
        row = np.array([[float(features.get(name, 0.0)) for name in self.feature_names]])
        probs = self.model.predict_proba(row)[0]
        idx = int(probs.argmax())

        shap_values = []
        shap_ok = False
        try:
            explainer = shap.TreeExplainer(self.model)
            sv = explainer.shap_values(pd.DataFrame([features.get(n, 0.0) for n in self.feature_names], columns=self.feature_names))
            if isinstance(sv, list):
                sv = sv[idx]
            sv = np.asarray(sv).flatten()
            for name, value in zip(self.feature_names, sv):
                shap_values.append(
                    {
                        "feature": name,
                        "value": features.get(name, 0.0),
                        "shap": round(float(value), 4),
                    }
                )
            shap_values.sort(key=lambda s: abs(s["shap"]), reverse=True)
            shap_ok = True
        except Exception as exc:
            logger.warning("SHAP explanation failed: %s", exc)

        return {
            "label": labels[idx],
            "confidence": round(probs[idx], 4),
            "probabilities": {c: round(float(p), 4) for c, p in zip(labels, probs)},
            "is_demo": False,
            "model_version": f"tabular-{self.model_path.stem}",
            "explanation": {
                "type": "shap",
                "shap_values": shap_values[:8] if shap_values else [],
                "shap_available": shap_ok,
            },
        }

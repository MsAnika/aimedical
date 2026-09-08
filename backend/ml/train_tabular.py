import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.services.ml.base import DISEASES

COLUMN_MAP = {
    "diabetes": {
        "pregnancies": ["preg", "pregnancies"],
        "glucose": ["plas", "glucose", "plasma_glucose"],
        "blood_pressure": ["pres", "blood_pressure", "bloodpressure"],
        "skin_thickness": ["skin", "skin_thickness"],
        "insulin": ["insu", "insulin"],
        "bmi": ["mass", "bmi"],
        "diabetes_pedigree": ["pedi", "diabetes_pedigree", "diabetespedigreefunction"],
        "age": ["age"],
    },
    "heart": {
        "age": ["age"],
        "sex": ["sex"],
        "cp": ["cp", "chest_pain_type", "chest"],
        "trestbps": ["trestbps", "resting_blood_pressure"],
        "chol": ["chol", "cholesterol", "serum_cholestoral"],
        "fbs": ["fbs", "fasting_blood_sugar"],
        "restecg": ["restecg", "resting_ecg", "resting_electrocardiographic_results"],
        "thalach": ["thalach", "max_heart_rate", "maximum_heart_rate_achieved"],
        "exang": ["exang", "exercise_induced_angina"],
        "oldpeak": ["oldpeak", "st_depression"],
        "slope": ["slope", "st_slope"],
        "ca": ["ca", "major_vessels", "number_of_major_vessels"],
        "thal": ["thal", "thalassemia"],
    },
}

TARGET_ALIASES = {
    "diabetes": ["class", "target", "diabetes"],
    "heart": ["num", "target", "disease", "heart_disease"],
}


def _load_data(disease: str, data_dir: Path) -> pd.DataFrame:
    candidates = [data_dir / f"{disease}.csv", data_dir / f"{disease}.csv.gz"]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        sys.exit(f"Dataset not found in {data_dir}. Run backend\\ml\\data\\download_{disease}.py first.")
    return pd.read_csv(path)


def _prepare(disease: str, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    target_col = None
    for alias in TARGET_ALIASES[disease]:
        if alias in df.columns:
            target_col = alias
            break
    if target_col is None:
        sys.exit(f"Could not find target column in {list(df.columns)}")

    y = df[target_col].astype(str)
    y = (y.str.lower().str.contains("yes|positive|1|tested_positive|true", regex=True)).astype(int)
    df = df.drop(columns=[target_col])

    mapping = COLUMN_MAP[disease]
    feature_names = [f.name for f in DISEASES[disease].features]
    X = pd.DataFrame()
    for name in feature_names:
        for alias in mapping[name]:
            if alias in df.columns:
                X[name] = pd.to_numeric(df[alias], errors="coerce")
                break
        else:
            sys.exit(f"Missing column for feature {name} in {list(df.columns)}")

    X = X.fillna(X.median())
    return X, y


def main() -> None:
    parser = argparse.ArgumentParser(description="Train tabular ML model (diabetes / heart)")
    parser.add_argument("disease", choices=["diabetes", "heart"])
    parser.add_argument("--data-dir", type=Path, default=Path("backend/ml/data"))
    parser.add_argument("--model", choices=["rf", "xgb"], default="xgb")
    parser.add_argument("--register", action="store_true", help="Record model version in the app database")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    spec = DISEASES[args.disease]
    out_dir = args.out or Path(get_settings().model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = _load_data(args.disease, args.data_dir)
    X, y = _prepare(args.disease, df)

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if args.model == "rf":
        model = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1)
    else:
        from xgboost import XGBClassifier

        model = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=42
        )

    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "precision": float(precision_score(y_test, preds, zero_division=0)),
        "recall": float(recall_score(y_test, preds, zero_division=0)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "test_size": int(len(y_test)),
    }
    print(json.dumps(metrics, indent=2))

    model_path = out_dir / spec.model_file
    metadata_path = out_dir / spec.metadata_file
    import joblib

    joblib.dump(model, model_path)
    metadata_path.write_text(
        json.dumps(
            {
                "feature_names": list(X.columns),
                "classes": spec.classes,
                "model_type": args.model,
                "metrics": metrics,
            },
            indent=2,
        ),
        "utf-8",
    )
    print(f"Saved model to {model_path}")
    print(f"Saved metadata to {metadata_path}")

    if args.register:
        from app.core.database import SessionLocal
        from app.core.models import ModelVersion

        with SessionLocal() as session:
            session.add(
                ModelVersion(
                    disease=args.disease,
                    version=f"{args.model}-{model_path.stem}",
                    metrics=metrics,
                )
            )
            session.commit()
        print("Registered model version in database")


if __name__ == "__main__":
    main()
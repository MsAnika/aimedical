from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.models import Prediction, Report, User
from app.schemas.prediction import DiseaseModule, PredictionOut, TabularPredictionIn
from app.services.ml.base import DISEASES, FeatureSpec
from app.services.ml.registry import get_registry

router = APIRouter(prefix="/api", tags=["predictions"])


def _serialize(db: Session, p: Prediction) -> PredictionOut:
    base = PredictionOut.model_validate(p)
    settings = get_settings()
    base.input_image_url = _static_url(p.input_image_path)
    base.heatmap_url = _static_url(p.heatmap_path)
    report = db.query(Report).filter(Report.prediction_id == p.id).first()
    if report is not None:
        base.report_url = f"/api/reports/{report.id}/download"
    return base


def _static_url(path: str | None) -> str | None:
    if not path:
        return None
    name = Path(path).name
    if "/heatmaps/" in path.replace("\\", "/"):
        return f"/media/heatmaps/{name}"
    if "/images/" in path.replace("\\", "/"):
        return f"/media/images/{name}"
    return f"/media/{name}"


def _validate_tabular_features(disease: str, features: dict) -> dict:
    spec = DISEASES[disease]
    if spec.type != "tabular":
        raise HTTPException(status_code=400, detail="Disease is not tabular")
    clean: dict = {}
    for f in spec.features:
        if f.name not in features:
            if f.required:
                raise HTTPException(status_code=422, detail=f"Missing field: {f.name}")
            continue
        raw = features[f.name]
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail=f"Invalid value for {f.name}")
        if f.options is not None and value not in f.options:
            raise HTTPException(status_code=422, detail=f"Invalid option for {f.name}")
        if f.min is not None and value < f.min:
            raise HTTPException(status_code=422, detail=f"{f.name} below minimum {f.min}")
        if f.max is not None and value > f.max:
            raise HTTPException(status_code=422, detail=f"{f.name} above maximum {f.max}")
        clean[f.name] = value
    return clean


@router.get("/diseases", response_model=list[DiseaseModule])
def list_diseases(user: User = Depends(get_current_user)):
    registry = get_registry()
    result = []
    for spec in DISEASES.values():
        status, version = registry.status(spec.id)
        result.append(
            DiseaseModule(
                id=spec.id,
                name=spec.name,
                type=spec.type,
                description=spec.description,
                classes=spec.classes or None,
                fields=[
                    {
                        "name": f.name,
                        "label": f.label,
                        "type": f.type,
                        "required": f.required,
                        "options": [str(o) for o in f.options] if f.options else None,
                    }
                    for f in spec.features
                ]
                or None,
                model_status=status,
                model_version=version,
            )
        )
    return result


@router.post("/predictions/image", response_model=PredictionOut)
def predict_image(
    disease: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if disease not in DISEASES:
        raise HTTPException(status_code=400, detail="Unknown disease")
    spec = DISEASES[disease]
    if spec.type != "image":
        raise HTTPException(status_code=400, detail="Disease is not image-based")

    ext = Path(file.filename or "upload.png").suffix.lower() or ".png"
    settings = get_settings()
    image_dir = Path(settings.media_dir) / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / f"{uuid.uuid4().hex}{ext}"
    with image_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    result = get_registry().predict_image(disease, str(image_path))

    p = Prediction(
        user_id=user.id,
        disease=disease,
        input_type="image",
        input_image_path=str(image_path),
        heatmap_path=result.get("heatmap_path"),
        label=result["label"],
        confidence=result["confidence"],
        probabilities=result.get("probabilities"),
        explanation=result.get("explanation"),
        model_version=result.get("model_version", "unknown"),
        is_demo=result.get("is_demo", False),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    # Increment metrics
    from app import metrics as metrics_module
    disease_key = disease
    if disease_key in metrics_module.PREDICTION_COUNT:
        metrics_module.PREDICTION_COUNT[disease_key] += 1
    if result.get("is_demo", False):
        metrics_module.MODEL_DEMO_COUNT += 1
    return _serialize(db, p)


@router.post("/predictions/tabular", response_model=PredictionOut)
def predict_tabular(
    payload: TabularPredictionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.disease not in DISEASES:
        raise HTTPException(status_code=400, detail="Unknown disease")
    features = _validate_tabular_features(payload.disease, payload.features)
    result = get_registry().predict_tabular(payload.disease, features)

    p = Prediction(
        user_id=user.id,
        disease=payload.disease,
        input_type="tabular",
        input_text=features,
        label=result["label"],
        confidence=result["confidence"],
        probabilities=result.get("probabilities"),
        explanation=result.get("explanation"),
        model_version=result.get("model_version", "unknown"),
        is_demo=result.get("is_demo", False),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    # Increment metrics
    from app import metrics as metrics_module
    disease_key = payload.disease
    if disease_key in metrics_module.PREDICTION_COUNT:
        metrics_module.PREDICTION_COUNT[disease_key] += 1
    if result.get("is_demo", False):
        metrics_module.MODEL_DEMO_COUNT += 1
    return _serialize(db, p)


@router.get("/predictions/{prediction_id}", response_model=PredictionOut)
def get_prediction(prediction_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if p is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    if p.user_id != user.id and user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not allowed")
    return _serialize(db, p)

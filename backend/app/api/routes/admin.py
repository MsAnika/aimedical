from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.core.models import ModelVersion, Prediction, Report, User
from app.schemas.prediction import AdminStats

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
def stats(
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    by_role = dict(
        db.query(User.role, func.count(User.id)).group_by(User.role).all()
    )
    by_disease = dict(
        db.query(Prediction.disease, func.count(Prediction.id)).group_by(Prediction.disease).all()
    )
    versions = [
        {
            "id": v.id,
            "disease": v.disease,
            "version": v.version,
            "metrics": v.metrics,
            "created_at": v.created_at.isoformat(),
        }
        for v in db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).all()
    ]
    return AdminStats(
        users=db.query(User).count(),
        predictions=db.query(Prediction).count(),
        reports=db.query(Report).count(),
        by_role=by_role,
        by_disease=by_disease,
        demo_predictions=db.query(Prediction).filter(Prediction.is_demo.is_(True)).count(),
        model_versions=versions,
    )
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.predictions import _serialize
from app.core.database import get_db
from app.core.models import Prediction, User
from app.schemas.prediction import HistoryOut

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryOut)
def history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = db.query(Prediction).filter(Prediction.user_id == user.id).order_by(Prediction.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return HistoryOut(total=total, items=[_serialize(db, p) for p in items])

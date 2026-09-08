from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.models import Prediction, Report, User
from app.schemas.prediction import ReportOut
from app.services.report import generate_report

router = APIRouter(prefix="/api", tags=["reports"])


def _ownership(prediction_id: int, user: User, db: Session) -> Prediction:
    p = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if p is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    if p.user_id != user.id and user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not allowed")
    return p


@router.post("/predictions/{prediction_id}/report", response_model=ReportOut)
def create_report(prediction_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _ownership(prediction_id, user, db)
    existing = db.query(Report).filter(Report.prediction_id == p.id).first()
    if existing is not None:
        return ReportOut(detail="Report already exists", report_id=existing.id, download_url=f"/api/reports/{existing.id}/download")
    path = generate_report(p)
    report = Report(prediction_id=p.id, file_path=str(path))
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportOut(detail="Report generated", report_id=report.id, download_url=f"/api/reports/{report.id}/download")


@router.get("/reports/{report_id}/download")
def download_report(report_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    _ownership(report.prediction_id, user, db)
    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file missing")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
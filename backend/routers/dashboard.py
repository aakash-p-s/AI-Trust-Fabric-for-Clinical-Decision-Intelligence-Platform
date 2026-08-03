"""
backend/routers/dashboard.py
GET /dashboard/summary -- powers the four top metric cards. See PRD Section 10.6.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.models import DigitalTwinRow, DriftAlertRow
from backend.models.schemas import DashboardSummary
from backend.routers.deps import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    rows = db.query(DigitalTwinRow).all()
    total = len(rows)
    flagged = sum(1 for r in rows if r.flagged)
    avg_conf = (
        sum(r.prediction.get("confidence", 0.0) for r in rows) / total if total else 0.0
    )
    active_alerts = (
        db.query(DriftAlertRow).filter(DriftAlertRow.status == "Active").count()
    )
    return DashboardSummary(
        total_predictions=total,
        flagged_count=flagged,
        flagged_pct=round(100.0 * flagged / total, 2) if total else 0.0,
        avg_confidence=round(avg_conf, 4),
        active_drift_alerts=active_alerts,
    )

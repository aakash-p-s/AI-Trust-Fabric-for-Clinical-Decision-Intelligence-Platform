"""
backend/routers/trust_monitoring.py
GET /trust-monitoring/summary, POST /trust-monitoring/run-now,
GET /trust-monitoring/alerts. See PRD Section 10.5.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.models import DriftAlertRow
from backend.models.schemas import (
    DriftAlert,
    DriftAlertListResponse,
    TrustMonitoringRunNowResponse,
    TrustMonitoringSummary,
)
from backend.routers.deps import get_db
from backend.services import drift_service
from backend.trust_monitoring import monitor as trust_monitor

router = APIRouter(prefix="/trust-monitoring", tags=["trust-monitoring"])


@router.get("/summary", response_model=TrustMonitoringSummary)
def get_summary(model_version: Optional[str] = None, db: Session = Depends(get_db)):
    trends = drift_service.compute_trends(db, model_version=model_version)
    latest_alert = (
        db.query(DriftAlertRow)
        .filter(DriftAlertRow.status == "Active")
        .order_by(DriftAlertRow.detected_at.desc())
        .first()
    )
    return TrustMonitoringSummary(
        confidence_trend=trends["confidence_trend"],
        flag_rate_trend=trends["flag_rate_trend"],
        avg_confidence_latest=trends["avg_confidence_latest"],
        avg_confidence_delta_pct=trends["avg_confidence_delta_pct"],
        pct_flagged_latest=trends["pct_flagged_latest"],
        pct_flagged_delta_pp=trends["pct_flagged_delta_pp"],
        total_predictions_in_range=trends["total_predictions_in_range"],
        drift_status=trends["drift_status"],
        drift_since=latest_alert.detected_at.isoformat() if (latest_alert and trends["drift_status"] == "Drift Detected") else None,
    )


@router.post("/run-now", response_model=TrustMonitoringRunNowResponse)
def run_now(model_version: Optional[str] = None, db: Session = Depends(get_db)):
    result = trust_monitor.run_trust_check(db, model_version=model_version)
    return TrustMonitoringRunNowResponse(**result)


@router.get("/alerts", response_model=DriftAlertListResponse)
def list_alerts(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(DriftAlertRow)
        .order_by(DriftAlertRow.detected_at.desc())
        .limit(limit)
        .all()
    )
    return DriftAlertListResponse(
        alerts=[
            DriftAlert(
                id=r.id,
                model_version=r.model_version,
                alert_type=r.alert_type,
                message=r.message,
                severity=r.severity,
                status=r.status,
                detected_at=r.detected_at,
            )
            for r in rows
        ]
    )

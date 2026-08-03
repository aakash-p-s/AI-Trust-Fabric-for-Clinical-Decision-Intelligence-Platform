"""
backend/trust_monitoring/monitor.py
-----------------------------------------------------
Deliberately implemented OUTSIDE the LangGraph pipeline, as a standalone
scheduled function, because it operates on many stored twins at once (an
aggregate computation over time) rather than processing one prediction
through a sequential agent chain. Registered with APScheduler in
backend/main.py on startup (default interval: 6 hours), and also callable
synchronously from POST /trust-monitoring/run-now.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.db.models import DriftAlertRow
from backend.services import drift_service

logger = logging.getLogger(__name__)


def run_trust_check(db: Session, model_version: str | None = None) -> dict:
    trends = drift_service.compute_trends(db, model_version=model_version)
    new_alerts: list[DriftAlertRow] = []

    target_version = model_version or "all_versions"

    if trends["confidence_drift_triggered"]:
        alert = DriftAlertRow(
            model_version=target_version,
            alert_type="confidence_drop",
            message=(
                f"Confidence dropped {trends['avg_confidence_delta_pct']:.0f}% "
                f"this week for {target_version}."
            ),
            severity="High",
            status="Active",
        )
        db.add(alert)
        new_alerts.append(alert)
        logger.warning("[trust_monitoring] confidence_drop alert for %s", target_version)

    if trends["flag_rate_drift_triggered"]:
        alert = DriftAlertRow(
            model_version=target_version,
            alert_type="flag_rate_rise",
            message=(
                f"Flag rate exceeded {drift_service.FLAG_RATE_THRESHOLD_PCT:.0f}% "
                f"threshold for {target_version}."
            ),
            severity="High",
            status="Active",
        )
        db.add(alert)
        new_alerts.append(alert)
        logger.warning("[trust_monitoring] flag_rate_rise alert for %s", target_version)

    if not new_alerts:
        alert = DriftAlertRow(
            model_version=target_version,
            alert_type="freshness_ok",
            message="Data freshness and drift metrics within expected range.",
            severity="Low",
            status="Cleared",
        )
        db.add(alert)
        new_alerts.append(alert)

    db.commit()
    for alert in new_alerts:
        db.refresh(alert)

    drift_since = datetime.now(timezone.utc).isoformat() if trends["drift_status"] == "Drift Detected" else None

    return {
        "confidence_trend": trends["confidence_trend"],
        "flag_rate_trend": trends["flag_rate_trend"],
        "avg_confidence_latest": trends["avg_confidence_latest"],
        "avg_confidence_delta_pct": trends["avg_confidence_delta_pct"],
        "pct_flagged_latest": trends["pct_flagged_latest"],
        "pct_flagged_delta_pp": trends["pct_flagged_delta_pp"],
        "total_predictions_in_range": trends["total_predictions_in_range"],
        "drift_status": trends["drift_status"],
        "drift_since": drift_since,
        "new_alerts": [
            {
                "id": a.id,
                "model_version": a.model_version,
                "alert_type": a.alert_type,
                "message": a.message,
                "severity": a.severity,
                "status": a.status,
                "detected_at": a.detected_at,
            }
            for a in new_alerts
        ],
    }

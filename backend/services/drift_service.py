"""
backend/services/drift_service.py
Computes confidence-trend and flag-rate-trend series over a date window,
and determines whether drift thresholds have been crossed. Used both by
GET /trust-monitoring/summary (read-only) and by
backend/trust_monitoring/monitor.py (which additionally writes
drift_alerts rows). See PRD Section 15.3 for the exact rule thresholds.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.db.models import DigitalTwinRow

CONFIDENCE_DROP_THRESHOLD_PCT = 15.0
FLAG_RATE_THRESHOLD_PCT = 10.0
DEFAULT_WINDOW_DAYS = 7


def _day_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def compute_trends(
    db: Session,
    model_version: Optional[str] = None,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)

    query = db.query(DigitalTwinRow).filter(DigitalTwinRow.twin_created_at >= since)
    rows = query.all()
    if model_version:
        rows = [r for r in rows if r.prediction.get("model_version") == model_version]

    by_day_conf: dict[str, list[float]] = defaultdict(list)
    by_day_flag: dict[str, list[bool]] = defaultdict(list)

    for row in rows:
        day = _day_key(row.twin_created_at)
        by_day_conf[day].append(row.prediction.get("confidence", 0.0))
        by_day_flag[day].append(bool(row.flagged))

    days_sorted = sorted(by_day_conf.keys())

    confidence_trend = [
        {"date": d, "avg_confidence": sum(by_day_conf[d]) / len(by_day_conf[d])}
        for d in days_sorted
    ]
    flag_rate_trend = [
        {"date": d, "pct_flagged": 100.0 * sum(by_day_flag[d]) / len(by_day_flag[d])}
        for d in days_sorted
    ]

    total_predictions = len(rows)

    if confidence_trend:
        conf_start = confidence_trend[0]["avg_confidence"]
        conf_latest = confidence_trend[-1]["avg_confidence"]
        conf_delta_pct = (
            100.0 * (conf_start - conf_latest) / conf_start if conf_start else 0.0
        )
    else:
        conf_latest, conf_delta_pct = 0.0, 0.0

    if flag_rate_trend:
        flag_start = flag_rate_trend[0]["pct_flagged"]
        flag_latest = flag_rate_trend[-1]["pct_flagged"]
        flag_delta_pp = flag_latest - flag_start
    else:
        flag_latest, flag_delta_pp = 0.0, 0.0

    confidence_drift = conf_delta_pct >= CONFIDENCE_DROP_THRESHOLD_PCT
    flag_rate_drift = flag_latest > FLAG_RATE_THRESHOLD_PCT

    drift_status = "Drift Detected" if (confidence_drift or flag_rate_drift) else "Normal"

    return {
        "confidence_trend": confidence_trend,
        "flag_rate_trend": flag_rate_trend,
        "avg_confidence_latest": round(conf_latest, 4),
        "avg_confidence_delta_pct": round(conf_delta_pct, 2),
        "pct_flagged_latest": round(flag_latest, 2),
        "pct_flagged_delta_pp": round(flag_delta_pp, 2),
        "total_predictions_in_range": total_predictions,
        "drift_status": drift_status,
        "confidence_drift_triggered": confidence_drift,
        "flag_rate_drift_triggered": flag_rate_drift,
    }

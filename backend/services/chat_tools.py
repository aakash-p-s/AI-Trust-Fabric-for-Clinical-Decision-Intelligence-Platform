"""
backend/services/chat_tools.py
The tools the AI Governance Assistant is allowed to call. Each one wraps
an EXISTING service function -- not new query logic -- so the chatbot can
never see or say anything the REST API itself couldn't already tell it.
"""
from langchain_core.tools import tool

from backend.db import session as db_session_module
from backend.db.models import DigitalTwinRow, DriftAlertRow, Patient
from backend.services import drift_service, rulebook_service


def _twin_row_to_dict(row: DigitalTwinRow) -> dict:
    return {
        "twin_id": row.twin_id,
        "patient_id": row.patient_id,
        "prediction": row.prediction,
        "lineage": row.lineage,
        "compliance": row.compliance,
        "explanation": row.explanation,
        "flagged": row.flagged,
        "twin_created_at": row.twin_created_at.isoformat() if row.twin_created_at else None,
        "review": row.review,
    }


@tool
def get_twin_by_patient_id(patient_id: str) -> dict:
    """Look up the full Digital Compliance Twin for one specific patient,
    by their patient ID (e.g. 'P0009'). Returns the prediction, confidence,
    compliance check results (including WHY it was flagged, if it was),
    the explanation, and review status if any. Use this whenever the user
    asks about a specific named patient, including "why was X flagged" or
    "what did the AI say about X"."""
    db = db_session_module.SessionLocal()
    try:
        row = (
            db.query(DigitalTwinRow)
            .filter(DigitalTwinRow.patient_id == patient_id)
            .order_by(DigitalTwinRow.twin_created_at.desc())
            .first()
        )
        if row is None:
            return {"error": f"No digital twin found for patient_id '{patient_id}'."}
        patient = db.get(Patient, patient_id)
        result = _twin_row_to_dict(row)
        if patient:
            result["patient_context"] = {
                "age": patient.age,
                "symptoms": patient.symptoms,
                "relevant_history": patient.relevant_history,
            }
        return result
    finally:
        db.close()


@tool
def list_flagged_twins(limit: int = 10) -> list[dict]:
    """List patients whose predictions are currently flagged for human
    review, most recent first. Use this for questions like 'show flagged
    patients' or 'what needs review right now'."""
    db = db_session_module.SessionLocal()
    try:
        rows = (
            db.query(DigitalTwinRow)
            .filter(DigitalTwinRow.flagged.is_(True))
            .order_by(DigitalTwinRow.twin_created_at.desc())
            .limit(limit)
            .all()
        )
        return [_twin_row_to_dict(r) for r in rows]
    finally:
        db.close()


@tool
def search_twins_by_patient_id(query: str, limit: int = 10) -> list[dict]:
    """Search for patients whose ID contains the given text. Use this when
    the user gives a partial patient ID or wants to browse rather than ask
    about one specific known patient."""
    db = db_session_module.SessionLocal()
    try:
        rows = (
            db.query(DigitalTwinRow)
            .filter(DigitalTwinRow.patient_id.ilike(f"%{query}%"))
            .order_by(DigitalTwinRow.twin_created_at.desc())
            .limit(limit)
            .all()
        )
        return [_twin_row_to_dict(r) for r in rows]
    finally:
        db.close()


@tool
def get_current_rulebook() -> dict:
    """Get the current compliance rulebook: which model versions are
    approved, the minimum confidence threshold, and which conditions
    always require human review regardless of confidence. Use this for
    questions about rules, thresholds, or why the compliance checks work
    the way they do."""
    db = db_session_module.SessionLocal()
    try:
        row = rulebook_service.get_rulebook(db)
        return {
            "approved_model_versions": row.approved_model_versions,
            "minimum_confidence_threshold": row.minimum_confidence_threshold,
            "high_risk_conditions_requiring_review": row.high_risk_conditions_requiring_review,
        }
    finally:
        db.close()


@tool
def get_trust_monitoring_summary(model_version: str = "") -> dict:
    """Get a summary of system trust health: confidence trend, flag-rate
    trend, and whether drift has been detected, optionally filtered to one
    model version. Use this for questions about drift, confidence trends,
    or overall system health."""
    db = db_session_module.SessionLocal()
    try:
        trends = drift_service.compute_trends(db, model_version=model_version or None)
        return {
            "avg_confidence_latest": trends["avg_confidence_latest"],
            "avg_confidence_delta_pct": trends["avg_confidence_delta_pct"],
            "pct_flagged_latest": trends["pct_flagged_latest"],
            "total_predictions_in_range": trends["total_predictions_in_range"],
            "drift_status": trends["drift_status"],
        }
    finally:
        db.close()


@tool
def get_recent_drift_alerts(limit: int = 5) -> list[dict]:
    """Get the most recent drift/trust monitoring alerts, most recent
    first. Use this when the user asks about specific alerts, not just the
    overall trend summary."""
    db = db_session_module.SessionLocal()
    try:
        rows = (
            db.query(DriftAlertRow)
            .order_by(DriftAlertRow.detected_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "model_version": r.model_version,
                "alert_type": r.alert_type,
                "message": r.message,
                "severity": r.severity,
                "status": r.status,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


ALL_TOOLS = [
    get_twin_by_patient_id,
    list_flagged_twins,
    search_twins_by_patient_id,
    get_current_rulebook,
    get_trust_monitoring_summary,
    get_recent_drift_alerts,
]

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}

"""
backend/routers/governance.py
GET /governance/summary and GET /governance/patient-processing-log --
read-only aggregations over digital_twins.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.models import DigitalTwinRow
from backend.models.schemas import (
    GovernanceSummary,
    PatientProcessingLogEntry,
    PatientProcessingLogResponse,
)
from backend.routers.deps import get_db

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/summary", response_model=GovernanceSummary)
def get_governance_summary(db: Session = Depends(get_db)):
    rows = db.query(DigitalTwinRow).all()
    total = len(rows)
    if total == 0:
        return GovernanceSummary(
            total_processed=0, avg_total_time_ms=0.0, avg_explainability_ms=0.0,
            total_tokens=0, rag_live_rate_pct=0.0, fallback_rate_pct=0.0,
        )

    total_times = []
    explainability_times = []
    total_tokens = 0
    rag_live_count = 0
    fallback_count = 0

    for row in rows:
        durations = row.stage_durations_ms or {}
        if durations:
            total_times.append(sum(durations.values()))
        if "explainability" in durations:
            explainability_times.append(durations["explainability"])

        cascade = row.explanation_cascade or {}
        usage = cascade.get("token_usage") or {}
        total_tokens += usage.get("total_tokens", 0)
        if cascade.get("final_source") and cascade["final_source"] != "primary_llm":
            fallback_count += 1

        rag = row.rag_details or {}
        if rag.get("status") == "live":
            rag_live_count += 1

    return GovernanceSummary(
        total_processed=total,
        avg_total_time_ms=round(sum(total_times) / len(total_times), 1) if total_times else 0.0,
        avg_explainability_ms=round(sum(explainability_times) / len(explainability_times), 1)
        if explainability_times else 0.0,
        total_tokens=total_tokens,
        rag_live_rate_pct=round(100.0 * rag_live_count / total, 1),
        fallback_rate_pct=round(100.0 * fallback_count / total, 1),
    )


@router.get("/patient-processing-log", response_model=PatientProcessingLogResponse)
def get_patient_processing_log(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(DigitalTwinRow)
        .order_by(DigitalTwinRow.twin_created_at.desc())
        .limit(limit)
        .all()
    )
    entries = []
    for row in rows:
        durations = row.stage_durations_ms or {}
        entries.append(
            PatientProcessingLogEntry(
                twin_id=row.twin_id,
                patient_id=row.patient_id,
                stage_durations_ms=durations,
                total_duration_ms=sum(durations.values()) if durations else 0,
                rag_details=row.rag_details,
                explanation_cascade=row.explanation_cascade,
                flagged=row.flagged,
                review=row.review,
                twin_created_at=row.twin_created_at,
            )
        )
    return PatientProcessingLogResponse(entries=entries)

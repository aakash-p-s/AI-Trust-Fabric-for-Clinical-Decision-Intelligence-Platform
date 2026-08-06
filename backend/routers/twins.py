"""
backend/routers/twins.py
GET /twins (Dashboard table), GET /twins/{twin_id} (Twin Detail),
POST /twins/{twin_id}/review (Approve/Override). See PRD Section 10.3.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.models import DigitalTwinRow, Patient
from backend.models.schemas import (
    DigitalTwin,
    DigitalTwinDetail,
    PatientContext,
    PredictionSummary,
    ReviewRequest,
    TwinListResponse,
    TwinSummary,
)
from backend.routers.deps import get_db, require_role
from backend.services import audit_service

router = APIRouter(prefix="/twins", tags=["twins"])


@router.get("", response_model=TwinListResponse)
def list_twins(
    status: str = Query("all", pattern="^(all|cleared|flagged)$"),
    model_version: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("twin_created_at", pattern="^(confidence|twin_created_at)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(DigitalTwinRow)

    if status == "cleared":
        query = query.filter(DigitalTwinRow.flagged.is_(False))
    elif status == "flagged":
        query = query.filter(DigitalTwinRow.flagged.is_(True))

    if search:
        query = query.filter(DigitalTwinRow.patient_id.ilike(f"%{search}%"))

    rows = query.all()

    if model_version:
        rows = [r for r in rows if r.prediction.get("model_version") == model_version]

    reverse = sort_dir == "desc"
    if sort_by == "confidence":
        rows.sort(key=lambda r: r.prediction.get("confidence", 0.0), reverse=reverse)
    else:
        rows.sort(key=lambda r: r.twin_created_at, reverse=reverse)

    total = len(rows)
    start = (page - 1) * limit
    page_rows = rows[start : start + limit]

    summaries = [
        TwinSummary(
            twin_id=r.twin_id,
            patient_id=r.patient_id,
            prediction=PredictionSummary(**r.prediction),
            flagged=r.flagged,
            review=r.review,
            twin_created_at=r.twin_created_at,
        )
        for r in page_rows
    ]
    return TwinListResponse(total=total, page=page, limit=limit, twins=summaries)


@router.get("/{twin_id}", response_model=DigitalTwinDetail)
def get_twin(twin_id: str, db: Session = Depends(get_db)):
    row = db.get(DigitalTwinRow, twin_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Twin not found")

    patient = db.get(Patient, row.patient_id)
    patient_ctx = PatientContext(
        patient_id=patient.patient_id,
        age=patient.age,
        symptoms=patient.symptoms,
        scan_type=patient.scan_type,
        relevant_history=patient.relevant_history,
    )

    return DigitalTwinDetail(
        **_twin_fields(row),
        patient=patient_ctx,
    )


@router.post("/{twin_id}/review", response_model=DigitalTwin)
def review_twin(
    twin_id: str,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    _role: str = Depends(require_role("compliance_governance")),
):
    row = db.get(DigitalTwinRow, twin_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Twin not found")

    if row.review is not None:
        raise HTTPException(status_code=409, detail="This twin has already been reviewed.")

    if payload.decision == "override" and not payload.notes.strip():
        raise HTTPException(status_code=400, detail="Override requires a non-empty reason.")

    review_record = {
        "reviewed_by": payload.reviewer_username,
        "decision": payload.decision,
        "notes": payload.notes,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    row.review = review_record
    db.commit()
    db.refresh(row)

    audit_service.write_audit_entry(
        db,
        entity_type="twin",
        entity_id=twin_id,
        action="twin_reviewed",
        actor=payload.reviewer_username,
        details={"decision": payload.decision, "notes": payload.notes},
    )

    return DigitalTwin(**_twin_fields(row))


def _twin_fields(row: DigitalTwinRow) -> dict:
    return {
        "twin_id": row.twin_id,
        "patient_id": row.patient_id,
        "prediction": row.prediction,
        "lineage": row.lineage,
        "compliance": row.compliance,
        "explanation": row.explanation,
        "explanation_type": row.explanation_type,
        "grounded_in_sources": row.grounded_in_sources,
        "low_grounding_confidence": row.low_grounding_confidence,
        "explanation_cascade": row.explanation_cascade,
        "rag_details": row.rag_details,
        "stage_durations_ms": row.stage_durations_ms,
        "flagged": row.flagged,
        "twin_created_at": row.twin_created_at,
        "review": row.review,
    }

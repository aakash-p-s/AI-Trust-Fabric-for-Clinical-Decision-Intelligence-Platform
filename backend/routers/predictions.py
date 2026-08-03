# """
# backend/routers/predictions.py
# POST /predictions -- runs the full LangGraph pipeline synchronously and
# returns the completed Digital Compliance Twin. See PRD Section 10.2.
# """
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from backend.agents.graph import run_trust_fabric_pipeline
# from backend.db.models import DigitalTwinRow, Patient, PredictionRow
# from backend.models.schemas import DigitalTwin, PredictionInput
# from backend.routers.deps import get_db
# from backend.services import audit_service, rulebook_service

# router = APIRouter(prefix="/predictions", tags=["predictions"])


# @router.post("", response_model=DigitalTwin, status_code=201)
# def create_prediction(payload: PredictionInput, db: Session = Depends(get_db)):
#     patient = db.get(Patient, payload.patient_id)
#     if patient is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Unknown patient_id: {payload.patient_id}. "
#             "Patient context must be seeded first.",
#         )

#     rulebook_row = rulebook_service.get_rulebook(db)
#     rulebook_dict = {
#         "approved_model_versions": rulebook_row.approved_model_versions,
#         "minimum_confidence_threshold": rulebook_row.minimum_confidence_threshold,
#         "high_risk_conditions_requiring_review": rulebook_row.high_risk_conditions_requiring_review,
#     }
#     patient_dict = {
#         "patient_id": patient.patient_id,
#         "age": patient.age,
#         "symptoms": patient.symptoms,
#         "scan_type": patient.scan_type,
#         "relevant_history": patient.relevant_history,
#     }
#     prediction_dict = payload.model_dump(mode="json")

#     twin_dict = run_trust_fabric_pipeline(prediction_dict, patient_dict, rulebook_dict)

#     # Persist the raw prediction (audit trail of what was ingested)
#     db.add(
#         PredictionRow(
#             id=twin_dict["twin_id"],  # 1:1 with the twin it produced
#             patient_id=payload.patient_id,
#             model_name=payload.model_name,
#             model_version=payload.model_version,
#             prediction=payload.prediction,
#             confidence=payload.confidence,
#             timestamp=payload.timestamp,
#         )
#     )

#     # Persist the twin
#     twin_row = DigitalTwinRow(
#         twin_id=twin_dict["twin_id"],
#         patient_id=twin_dict["patient_id"],
#         prediction=twin_dict["prediction"],
#         lineage=twin_dict["lineage"],
#         compliance=twin_dict["compliance"],
#         explanation=twin_dict["explanation"],
#         explanation_type=twin_dict["explanation_type"],
#         grounded_in_sources=twin_dict["grounded_in_sources"],
#         low_grounding_confidence=twin_dict["low_grounding_confidence"],
#         flagged=twin_dict["flagged"],
#         review=None,
#     )
#     db.add(twin_row)
#     db.commit()
#     db.refresh(twin_row)

#     audit_service.write_audit_entry(
#         db,
#         entity_type="twin",
#         entity_id=twin_row.twin_id,
#         action="twin_created",
#         actor="system",
#         details={"model_version": payload.model_version, "flagged": twin_row.flagged},
#     )

#     return _row_to_twin(twin_row)


# def _row_to_twin(row: DigitalTwinRow) -> DigitalTwin:
#     return DigitalTwin(
#         twin_id=row.twin_id,
#         patient_id=row.patient_id,
#         prediction=row.prediction,
#         lineage=row.lineage,
#         compliance=row.compliance,
#         explanation=row.explanation,
#         explanation_type=row.explanation_type,
#         grounded_in_sources=row.grounded_in_sources,
#         low_grounding_confidence=row.low_grounding_confidence,
#         flagged=row.flagged,
#         twin_created_at=row.twin_created_at,
#         review=row.review,
#     )
"""
backend/routers/predictions.py
POST /predictions -- runs the full LangGraph pipeline synchronously and
returns the completed Digital Compliance Twin. See PRD Section 10.2.

Also provides a streaming variant (POST /predictions/stream +
GET /predictions/stream/{request_id}/status) that runs the identical
pipeline via LangGraph's .stream() API in a background thread, updating
an in-memory progress tracker (backend/services/progress_service.py)
after each of the 4 agents finishes. This lets the UI poll for and show
real, live per-stage progress instead of one long opaque wait -- added
because the synchronous endpoint above gives no visibility into which
stage is currently running while a request is in flight.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agents.graph import run_trust_fabric_pipeline, run_trust_fabric_pipeline_with_progress
from backend.db import session as db_session_module
from backend.db.models import DigitalTwinRow, Patient, PredictionRow
from backend.models.schemas import DigitalTwin, PredictionInput
from backend.routers.deps import get_db
from backend.services import audit_service, progress_service, rulebook_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _load_context(db: Session, payload: PredictionInput) -> tuple[dict, dict]:
    """Fetches the patient + current rulebook, or raises 404 if the patient
    is unknown. Shared by both the synchronous and streaming endpoints."""
    patient = db.get(Patient, payload.patient_id)
    if patient is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown patient_id: {payload.patient_id}. "
            "Patient context must be seeded first.",
        )

    rulebook_row = rulebook_service.get_rulebook(db)
    rulebook_dict = {
        "approved_model_versions": rulebook_row.approved_model_versions,
        "minimum_confidence_threshold": rulebook_row.minimum_confidence_threshold,
        "high_risk_conditions_requiring_review": rulebook_row.high_risk_conditions_requiring_review,
    }
    patient_dict = {
        "patient_id": patient.patient_id,
        "age": patient.age,
        "symptoms": patient.symptoms,
        "scan_type": patient.scan_type,
        "relevant_history": patient.relevant_history,
    }
    return patient_dict, rulebook_dict


def _persist_twin(db: Session, payload: PredictionInput, twin_dict: dict) -> DigitalTwinRow:
    """Writes the raw prediction + the assembled twin to the database, plus
    an audit log entry. Shared by both endpoints so there is exactly one
    place that defines what "a prediction was ingested" means in storage."""
    db.add(
        PredictionRow(
            id=twin_dict["twin_id"],
            patient_id=payload.patient_id,
            model_name=payload.model_name,
            model_version=payload.model_version,
            prediction=payload.prediction,
            confidence=payload.confidence,
            timestamp=payload.timestamp,
        )
    )

    twin_row = DigitalTwinRow(
        twin_id=twin_dict["twin_id"],
        patient_id=twin_dict["patient_id"],
        prediction=twin_dict["prediction"],
        lineage=twin_dict["lineage"],
        compliance=twin_dict["compliance"],
        explanation=twin_dict["explanation"],
        explanation_type=twin_dict["explanation_type"],
        grounded_in_sources=twin_dict["grounded_in_sources"],
        low_grounding_confidence=twin_dict["low_grounding_confidence"],
        flagged=twin_dict["flagged"],
        review=None,
    )
    db.add(twin_row)
    db.commit()
    db.refresh(twin_row)

    audit_service.write_audit_entry(
        db,
        entity_type="twin",
        entity_id=twin_row.twin_id,
        action="twin_created",
        actor="system",
        details={"model_version": payload.model_version, "flagged": twin_row.flagged},
    )
    return twin_row


# ---------------------------------------------------------------------------
# Synchronous endpoint (existing) -- used by scripts/, tests/, and anywhere
# that just wants the finished twin back in one response.
# ---------------------------------------------------------------------------
@router.post("", response_model=DigitalTwin, status_code=201)
def create_prediction(payload: PredictionInput, db: Session = Depends(get_db)):
    patient_dict, rulebook_dict = _load_context(db, payload)
    prediction_dict = payload.model_dump(mode="json")

    twin_dict = run_trust_fabric_pipeline(prediction_dict, patient_dict, rulebook_dict)
    twin_row = _persist_twin(db, payload, twin_dict)

    return _row_to_twin(twin_row)


# ---------------------------------------------------------------------------
# Streaming variant -- for live per-stage progress in the UI.
# ---------------------------------------------------------------------------
@router.post("/stream", status_code=202)
def start_prediction_stream(
    payload: PredictionInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Validate up front, in the request/response cycle, so a 404 for an
    # unknown patient comes back immediately rather than silently failing
    # inside the background thread.
    patient_dict, rulebook_dict = _load_context(db, payload)
    prediction_dict = payload.model_dump(mode="json")

    request_id = progress_service.start_tracking(payload.patient_id)
    background_tasks.add_task(
        _run_and_persist_in_background, request_id, payload, prediction_dict, patient_dict, rulebook_dict
    )

    return {"request_id": request_id, "status": "processing"}


def _run_and_persist_in_background(
    request_id: str,
    payload: PredictionInput,
    prediction_dict: dict,
    patient_dict: dict,
    rulebook_dict: dict,
) -> None:
    """Runs on a background thread (FastAPI BackgroundTasks). Opens its own
    DB session since the request-scoped one from Depends(get_db) is closed
    by the time this runs."""
    db = db_session_module.SessionLocal()
    try:
        twin_dict = run_trust_fabric_pipeline_with_progress(
            prediction_dict, patient_dict, rulebook_dict, request_id
        )
        twin_row = _persist_twin(db, payload, twin_dict)
        progress_service.mark_done(request_id, _row_to_twin(twin_row).model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001 -- surface any failure to the poller instead of losing it silently
        progress_service.mark_error(request_id, str(exc))
    finally:
        db.close()


@router.get("/stream/active")
def get_active_prediction_stream():
    """Returns whichever prediction is currently mid-pipeline, regardless of
    whether the browser or a script (scripts/run_demo_10_patients.py)
    started it. Returns {"active": null} if nothing is currently processing.
    This is what lets the Dashboard passively show live progress even when
    it never itself called POST /predictions/stream."""
    active = progress_service.get_most_recent_active()
    return {"active": active}


@router.get("/stream/{request_id}/status")
def get_prediction_stream_status(request_id: str):
    status = progress_service.get_status(request_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Unknown request_id")
    return status


def _row_to_twin(row: DigitalTwinRow) -> DigitalTwin:
    return DigitalTwin(
        twin_id=row.twin_id,
        patient_id=row.patient_id,
        prediction=row.prediction,
        lineage=row.lineage,
        compliance=row.compliance,
        explanation=row.explanation,
        explanation_type=row.explanation_type,
        grounded_in_sources=row.grounded_in_sources,
        low_grounding_confidence=row.low_grounding_confidence,
        flagged=row.flagged,
        twin_created_at=row.twin_created_at,
        review=row.review,
    )


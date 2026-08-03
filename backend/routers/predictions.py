"""
backend/routers/predictions.py
POST /predictions -- runs the full LangGraph pipeline synchronously and
returns the completed Digital Compliance Twin. See PRD Section 10.2.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agents.graph import run_trust_fabric_pipeline
from backend.db.models import DigitalTwinRow, Patient, PredictionRow
from backend.models.schemas import DigitalTwin, PredictionInput
from backend.routers.deps import get_db
from backend.services import audit_service, rulebook_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=DigitalTwin, status_code=201)
def create_prediction(payload: PredictionInput, db: Session = Depends(get_db)):
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
    prediction_dict = payload.model_dump(mode="json")

    twin_dict = run_trust_fabric_pipeline(prediction_dict, patient_dict, rulebook_dict)

    # Persist the raw prediction (audit trail of what was ingested)
    db.add(
        PredictionRow(
            id=twin_dict["twin_id"],  # 1:1 with the twin it produced
            patient_id=payload.patient_id,
            model_name=payload.model_name,
            model_version=payload.model_version,
            prediction=payload.prediction,
            confidence=payload.confidence,
            timestamp=payload.timestamp,
        )
    )

    # Persist the twin
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

    return _row_to_twin(twin_row)


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

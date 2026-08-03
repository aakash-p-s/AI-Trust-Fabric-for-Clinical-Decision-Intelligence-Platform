"""
backend/routers/patients.py
GET /patients/{patient_id}. See PRD Section 10.7.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.models import Patient
from backend.models.schemas import PatientContext
from backend.routers.deps import get_db

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}", response_model=PatientContext)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Unknown patient_id")
    return PatientContext(
        patient_id=patient.patient_id,
        age=patient.age,
        symptoms=patient.symptoms,
        scan_type=patient.scan_type,
        relevant_history=patient.relevant_history,
    )

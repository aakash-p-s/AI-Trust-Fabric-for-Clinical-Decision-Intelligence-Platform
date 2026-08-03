"""
backend/routers/demo.py
GET /demo/patients -- returns the curated 10-patient demo set (see
backend/demo_data.py) as ready-to-send PredictionInput records, so the
frontend's live "Send Demo Patient" panel doesn't need to duplicate this
list or hardcode prediction values of its own.
"""
import json
from pathlib import Path

from fastapi import APIRouter

from backend.demo_data import DEMO_PATIENT_IDS

router = APIRouter(prefix="/demo", tags=["demo"])

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@router.get("/patients")
def get_demo_patients():
    with open(DATA_DIR / "predictions.json") as f:
        all_predictions = {p["patient_id"]: p for p in json.load(f)}

    return {
        "patients": [all_predictions[pid] for pid in DEMO_PATIENT_IDS if pid in all_predictions]
    }

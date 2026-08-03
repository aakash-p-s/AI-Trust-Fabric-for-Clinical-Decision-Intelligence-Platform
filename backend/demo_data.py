"""
backend/demo_data.py
The curated 10-patient demo set, defined once here so both
scripts/run_demo_10_patients.py and GET /demo/patients (used by the
frontend's live "Send Demo Patient" panel) stay in sync -- previously
this list was hardcoded separately in the script only.

See scripts/run_demo_10_patients.py's original docstring for why each
patient is included; unchanged here, just centralized.
"""
DEMO_PATIENT_IDS = [
    "P0001", "P0002", "P0007", "P0011",  # cleared
    "P0009", "P0059", "P0003", "P0019", "P0030", "P0046",  # flagged, varied reasons
]

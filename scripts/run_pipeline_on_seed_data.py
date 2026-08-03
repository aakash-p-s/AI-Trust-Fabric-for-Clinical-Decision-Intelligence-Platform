"""
scripts/run_pipeline_on_seed_data.py
Pushes every seed prediction through POST /predictions, exactly as a real
ingestion event would. This is also the project's End-to-End smoke test:
all 60 seed predictions must process without error (PRD Section 19.3).

Requires the backend to be running at http://localhost:8000.
"""
import json
import sys
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
API_URL = "http://localhost:8000/predictions"


def main():
    with open(DATA_DIR / "predictions.json") as f:
        predictions = json.load(f)

    ok, failed, flagged = 0, 0, 0
    for record in predictions:
        response = requests.post(API_URL, json=record, timeout=90)
        if response.status_code == 201:
            ok += 1
            if response.json().get("flagged"):
                flagged += 1
        else:
            failed += 1
            print(f"FAILED {record['patient_id']}: {response.status_code} {response.text}")
        time.sleep(0.05)

    print(f"\nDone. {ok} succeeded, {failed} failed, {flagged} flagged for review.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
scripts/run_demo_10_patients.py
-----------------------------------------------------
A curated 10-patient subset of data/predictions.json, sent one at a time
with a deliberate delay, so you can watch each prediction appear live on
the Dashboard while this script runs -- rather than silently bulk-loading
all 60 seed predictions in the background before opening the browser.

The 10 patients are chosen to demonstrate every distinct compliance
outcome the system supports, not picked at random:

  Patient   Prediction   Version   Confidence   Why it's included
  -------   ----------   -------   ----------   -----------------
  P0001     NORMAL       v2.1      0.9631       Cleared -- everything passes
  P0002     NORMAL       v2.0      0.9656       Cleared -- different approved version
  P0007     NORMAL       v2.0      0.8484       Cleared -- solid but not top confidence
  P0011     NORMAL       v2.1      0.9053       Cleared
  P0009     PNEUMONIA    v2.1      0.8423       Flagged -- high-risk condition ONLY
                                                 (version approved, confidence fine)
  P0059     PNEUMONIA    v2.0      0.6347       Flagged -- high-risk condition AND
                                                 low confidence (two reasons at once)
  P0003     PNEUMONIA    v2.1      0.5805       Flagged -- high-risk + low confidence,
                                                 different version than P0059
  P0019     PNEUMONIA    v1.9      0.8387       Flagged -- high-risk AND unapproved
                                                 model version (two reasons)
  P0030     NORMAL       v1.9      0.8723       Flagged -- unapproved version ONLY
                                                 (a non-high-risk prediction still
                                                 gets flagged for governance reasons)
  P0046     NORMAL       v2.1      0.6202       Flagged -- low confidence ONLY
                                                 (an otherwise unremarkable NORMAL
                                                 reading that's simply not confident
                                                 enough to auto-clear)

That's every combination the Compliance Agent can produce: 4 cleared
cases, and 6 flagged cases covering each of the three rules individually
and in combination.

Requires the backend to be running at http://localhost:8000.
"""
import json
import sys
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
API_URL = "http://localhost:8000/predictions"

DEMO_PATIENT_IDS = [
    "P0001", "P0002", "P0007", "P0011",  # cleared
    "P0009", "P0059", "P0003", "P0019", "P0030", "P0046",  # flagged, varied reasons
]

DELAY_SECONDS = 4  # pause between each so you can watch the Dashboard update


def main():
    with open(DATA_DIR / "predictions.json") as f:
        all_predictions = {p["patient_id"]: p for p in json.load(f)}

    missing = [pid for pid in DEMO_PATIENT_IDS if pid not in all_predictions]
    if missing:
        print(f"ERROR: these patient IDs are not in predictions.json: {missing}")
        sys.exit(1)

    print(f"Sending {len(DEMO_PATIENT_IDS)} predictions, one every {DELAY_SECONDS}s.")
    print("Keep the Dashboard open in your browser to watch them appear.\n")

    ok, failed, flagged = 0, 0, 0
    for i, pid in enumerate(DEMO_PATIENT_IDS, start=1):
        record = all_predictions[pid]
        print(f"[{i}/{len(DEMO_PATIENT_IDS)}] Sending {pid} "
              f"({record['prediction']}, {record['model_version']}, "
              f"conf={record['confidence']})...", end=" ", flush=True)

        try:
            response = requests.post(API_URL, json=record, timeout=90)
        except requests.exceptions.RequestException as exc:
            print(f"FAILED (request error: {exc})")
            failed += 1
            continue

        if response.status_code == 201:
            body = response.json()
            ok += 1
            if body.get("flagged"):
                flagged += 1
            print(f"OK -- {'FLAGGED' if body.get('flagged') else 'cleared'}")
        else:
            failed += 1
            print(f"FAILED ({response.status_code}): {response.text}")

        if i < len(DEMO_PATIENT_IDS):
            time.sleep(DELAY_SECONDS)

    print(f"\nDone. {ok} succeeded, {failed} failed, {flagged} flagged for review.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

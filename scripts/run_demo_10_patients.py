"""
scripts/run_demo_10_patients.py
-----------------------------------------------------
A curated 10-patient subset of data/predictions.json, sent one at a time
via the STREAMING endpoint (POST /predictions/stream), so the Dashboard's
"Now Processing" panel can show live per-stage progress for each patient
in real time -- purely by polling the backend, without the browser ever
having to be the thing that triggered the request.

This script itself also polls each patient's own status until it's done
before moving to the next one, so patients are still processed strictly
one at a time (matching the original behavior), and prints the stage
transitions to this terminal too, as a bonus.

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.demo_data import DEMO_PATIENT_IDS  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
START_URL = "http://localhost:8000/predictions/stream"
STATUS_URL_TEMPLATE = "http://localhost:8000/predictions/stream/{request_id}/status"

DELAY_BETWEEN_PATIENTS_SECONDS = 1.5  # brief pause after one finishes, before starting the next
POLL_INTERVAL_SECONDS = 0.4
POLL_TIMEOUT_SECONDS = 150


def process_one_patient(record: dict) -> dict:
    """Starts the streaming pipeline for one patient and polls until done,
    printing each stage transition. Returns the final status dict."""
    start_response = requests.post(START_URL, json=record, timeout=10)
    start_response.raise_for_status()
    request_id = start_response.json()["request_id"]

    seen_stages: set = set()
    deadline = time.time() + POLL_TIMEOUT_SECONDS

    while time.time() < deadline:
        status_response = requests.get(
            STATUS_URL_TEMPLATE.format(request_id=request_id), timeout=10
        )
        status_response.raise_for_status()
        status = status_response.json()

        for stage in status["completed_stages"]:
            if stage not in seen_stages:
                seen_stages.add(stage)
                print(f"    -> {stage} complete")

        if status["done"]:
            return status

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"This script gave up waiting after {POLL_TIMEOUT_SECONDS}s -- the LLM call "
        "may just be slow. The backend keeps processing regardless of this script's "
        "timeout, so the twin may still complete successfully; check the Dashboard "
        "or query GET /twins?search=<patient_id> to confirm."
    )


def main():
    with open(DATA_DIR / "predictions.json") as f:
        all_predictions = {p["patient_id"]: p for p in json.load(f)}

    missing = [pid for pid in DEMO_PATIENT_IDS if pid not in all_predictions]
    if missing:
        print(f"ERROR: these patient IDs are not in predictions.json: {missing}")
        sys.exit(1)

    print(f"Sending {len(DEMO_PATIENT_IDS)} predictions, one at a time, via the streaming endpoint.")
    print("Keep the Dashboard open in your browser -- the 'Now Processing' panel")
    print("will show each patient and stage live, with no action needed there.\n")

    ok, failed, flagged = 0, 0, 0
    for i, pid in enumerate(DEMO_PATIENT_IDS, start=1):
        record = all_predictions[pid]
        print(f"[{i}/{len(DEMO_PATIENT_IDS)}] {pid} "
              f"({record['prediction']}, {record['model_version']}, "
              f"conf={record['confidence']})")

        try:
            final_status = process_one_patient(record)
        except TimeoutError as exc:
            print(f"    TIMED OUT (this script gave up watching): {exc}")
            failed += 1
            continue
        except requests.exceptions.RequestException as exc:
            print(f"    FAILED (request error): {exc}")
            failed += 1
            continue

        if final_status["error"]:
            print(f"    FAILED: {final_status['error']}")
            failed += 1
        else:
            ok += 1
            twin_flagged = final_status["twin"]["flagged"]
            if twin_flagged:
                flagged += 1
            print(f"    DONE -- {'FLAGGED' if twin_flagged else 'cleared'}")

        if i < len(DEMO_PATIENT_IDS):
            time.sleep(DELAY_BETWEEN_PATIENTS_SECONDS)

    print(f"\nDone. {ok} succeeded, {failed} failed, {flagged} flagged for review.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

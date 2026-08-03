"""
backend/services/progress_service.py
-----------------------------------------------------
An in-memory tracker for "which pipeline stage is this in-flight request
currently on", so the frontend can poll GET /predictions/stream/{id}/status
and show real, live per-stage progress -- not a simulated progress bar.

Also tracks patient_id + a start timestamp per request, so the Dashboard
can discover "what's currently processing right now" via
GET /predictions/stream/active WITHOUT already knowing the request_id --
this is what lets a script (scripts/run_demo_10_patients.py) drive the
pipeline while the browser passively displays progress, rather than the
browser having to be the one that started the request.

Deliberately in-memory, not a database table: this data is transient
(only meaningful while a request is actively processing) and doesn't need
to survive a server restart. Keyed by a request_id generated fresh for
each streamed ingestion.

Thread-safety note: FastAPI runs synchronous "def" path operations in a
threadpool, so multiple requests (the POST that's processing, and the GET
polling for status) genuinely run concurrently on different threads. A
plain dict with atomic per-key writes is sufficient here (Python's GIL
makes individual dict item assignment atomic); a lock is added anyway for
clarity and to guard the read-modify-write in mark_stage_complete.
"""
import threading
import time
import uuid
from typing import Optional

STAGES_IN_ORDER = ["lineage", "compliance", "explainability", "twin_assembler"]
STALE_AFTER_SECONDS = 120

_lock = threading.Lock()
_progress: dict[str, dict] = {}


def start_tracking(patient_id: str) -> str:
    request_id = str(uuid.uuid4())
    with _lock:
        _progress[request_id] = {
            "request_id": request_id,
            "patient_id": patient_id,
            "current_stage": None,
            "completed_stages": [],
            "done": False,
            "error": None,
            "twin": None,
            "started_at": time.time(),
        }
    return request_id


def mark_stage_started(request_id: str, stage: str) -> None:
    with _lock:
        if request_id in _progress:
            _progress[request_id]["current_stage"] = stage


def mark_stage_complete(request_id: str, stage: str) -> None:
    with _lock:
        entry = _progress.get(request_id)
        if entry is not None and stage not in entry["completed_stages"]:
            entry["completed_stages"].append(stage)


def mark_done(request_id: str, twin: dict) -> None:
    with _lock:
        if request_id in _progress:
            _progress[request_id]["current_stage"] = "done"
            _progress[request_id]["done"] = True
            _progress[request_id]["twin"] = twin


def mark_error(request_id: str, error_message: str) -> None:
    with _lock:
        if request_id in _progress:
            _progress[request_id]["error"] = error_message
            _progress[request_id]["done"] = True


def get_status(request_id: str) -> Optional[dict]:
    with _lock:
        entry = _progress.get(request_id)
        return dict(entry) if entry is not None else None


def get_most_recent_active() -> Optional[dict]:
    """Returns the most recently started NOT-YET-DONE request, or None if
    nothing is currently (and recently) processing. Entries older than
    STALE_AFTER_SECONDS are excluded even if still technically not done --
    otherwise an abandoned/slow request keeps resurfacing as "the active
    one" forever, every time there's a brief gap between newer requests."""
    with _lock:
        now = time.time()
        active_entries = [
            e for e in _progress.values()
            if not e["done"] and (now - e["started_at"]) <= STALE_AFTER_SECONDS
        ]
        if not active_entries:
            return None
        most_recent = max(active_entries, key=lambda e: e["started_at"])
        return dict(most_recent)


"""
backend/main.py
FastAPI app: CORS, router mounting, startup events (DB connectivity check,
RAG knowledge base loading, APScheduler job registration). See PRD
Section 7.1.
"""
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.session import SessionLocal, init_engine
from backend.routers import auth, dashboard, demo, patients, predictions, rulebook, trust_monitoring, twins
from backend.services import rag_service
from backend.trust_monitoring.monitor import run_trust_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Autonomous AI Trust Fabric", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("CORS_ALLOWED_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(twins.router)
app.include_router(rulebook.router)
app.include_router(trust_monitoring.router)
app.include_router(patients.router)
app.include_router(dashboard.router)
app.include_router(demo.router)

_scheduler = BackgroundScheduler()


@app.on_event("startup")
def on_startup():
    # 1. Verify the Postgres (or SQLite) connection is reachable
    init_engine()
    logger.info("Database connection verified.")

    # 2. Load and embed the RAG knowledge base once; embeddings are cached
    #    in rag_service's module-level state for the lifetime of the process.
    rag_service.load_knowledge_base()
    logger.info("RAG knowledge base loaded.")

    # 3. Start the in-process scheduled Trust Monitoring job.
    #    NOT a LangGraph node -- see backend/trust_monitoring/monitor.py.
    interval_hours = float(os.environ.get("TRUST_MONITORING_INTERVAL_HOURS", "6"))

    def _scheduled_job():
        db = SessionLocal()
        try:
            run_trust_check(db)
        finally:
            db.close()

    _scheduler.add_job(_scheduled_job, "interval", hours=interval_hours, id="trust_monitoring_job")
    _scheduler.start()
    logger.info("Trust Monitoring scheduler started (every %s hours).", interval_hours)


@app.on_event("shutdown")
def on_shutdown():
    _scheduler.shutdown(wait=False)


@app.get("/health")
def health():
    return {"status": "ok"}

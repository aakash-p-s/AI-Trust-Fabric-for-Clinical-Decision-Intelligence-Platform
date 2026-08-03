# Autonomous AI Trust Fabric for Clinical Decision Intelligence

A Digital Compliance Twin platform that sits **after** an existing (black-box) diagnostic
AI model and automatically produces a permanent, auditable record for every prediction:
what data went in, whether it complies with hospital rules, and a plain-English,
RAG-grounded explanation of why the prediction is clinically reasonable.

This system does **not** build, train, or call a real diagnostic model. It consumes
mock prediction records shaped exactly like a real model's output (see
`data/predictions.json`).

Full build specification: see `PRD_Autonomous_AI_Trust_Fabric.docx`.

---

## 1. Prerequisites

- Python 3.11
- Node.js 20+
- Docker (only used for PostgreSQL — see note below)
- An OpenRouter API key (free tier works — `openai/gpt-oss-20b:free`)

## 2. Backend Setup

```bash
# 1. Clone and enter the project
cd trust_fabric

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY and DATABASE_URL

# 5. Start PostgreSQL (Docker)
docker compose up -d
# wait ~5 seconds for the healthcheck to pass

# 6. Initialize the database schema
python scripts/init_db.py

# 7. Seed demo data (patients, predictions, rulebook, knowledge base)
python scripts/seed_data.py

# 8. Run the backend
uvicorn backend.main:app --reload --port 8000
```

> **No Docker?** Point `DATABASE_URL` in `.env` at a local Postgres instance, or a
> SQLite file (e.g. `sqlite:///./trust_fabric.db`) — the ORM models are dialect-agnostic.

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open the app at **http://localhost:5173**. The backend must be running at
**http://localhost:8000** (configured via `frontend/.env.local` → `VITE_API_URL`).

## 4. Demo Logins

Authentication in this phase is intentionally simple — **no JWT, no Keycloak**.
Username/password are checked against a small hardcoded table, and the role
determines which pages/nav items are shown.

| Username | Password | Role | Sees |
|---|---|---|---|
| `dr.mitchell` | `clinician123` | Clinician | Dashboard (read-only), Twin Detail (read-only) |
| `compliance.lead` | `compliance123` | Compliance/Governance | Dashboard, Twin Detail (with Approve/Override), Rulebook Settings, Trust Monitoring |

## 5. Loading Sample Predictions

The 60 sample patients/predictions from `data/patients.json` and `data/predictions.json`
are loaded by `scripts/seed_data.py`. To push them through the full agent pipeline and
generate Digital Compliance Twins:

```bash
python scripts/run_pipeline_on_seed_data.py
```

This calls `POST /predictions` once per record, exactly as a real ingestion event would.

## 6. Running Tests

```bash
pytest tests/
```

## 7. What's Deliberately Not Included (Phase 1)

- No Kafka / message queue — predictions are ingested via direct HTTP POST
- No Airflow — the Trust Monitoring job runs on an in-process APScheduler
- No Keycloak / JWT — simple username+password → role lookup
- No cloud hosting — everything runs locally
- No real diagnostic model — predictions are mock data shaped like real model output
- No real FHIR/EHR integration

See Section 20 ("Future Extension Points") of the PRD for what each of these becomes
in a production deployment.

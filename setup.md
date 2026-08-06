# Setup Guide — Autonomous AI Trust Fabric

Use this every time you restart your machine and need to bring the system
back up. Follow the steps in order — don't skip the Docker/Postgres check,
that's the step most likely to silently break things after a reboot.

---

## 0. Prerequisites Check (30 seconds)

- [ ] Docker Desktop is installed
- [ ] You have your `.env` file already set up in the project root with real values for:
  - `OPENROUTER_API_KEY`
  - `GROQ_API_KEY`
  - `DATABASE_URL`

If `.env` is missing or you're not sure, check Step 7 below before continuing.

---

## Step 1 — Open PowerShell and Navigate to the Project

```powershell
cd C:\Users\Aakash\Documents\trust_fabric
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your prompt.

---

## Step 2 — Start Docker Desktop

Open Docker Desktop from the Start menu if it isn't already running. Wait
until the whale icon in your system tray stops animating and Docker
Desktop's window says **"Docker Desktop is running."**

---

## Step 3 — Check the Native Postgres Service Is Still Stopped

**This is the step most likely to bite you after a reboot.** Windows may
have re-enabled the native Postgres service.

```powershell
Get-Service -Name "postgresql-x64-18"
```

- If it shows **`Stopped`** → good, move to Step 4.
- If it shows **`Running`** → stop it again:

```powershell
Stop-Service -Name "postgresql-x64-18"
Set-Service -Name "postgresql-x64-18" -StartupType Manual
```

**Why this matters:** if this native service is running, it silently
occupies port 5432, and Docker's Postgres container either won't start
cleanly or your app will connect to the wrong database and get a
password-authentication error.

---

## Step 4 — Verify Port 5432 Is Clear

```powershell
netstat -ano | findstr :5432
```

You should see **at most one** process listed (Docker's). If you see
`postgres.exe` in the list too, go back to Step 3.

---

## Step 5 — Start Docker's Postgres Container

```powershell
docker compose up -d
```

Wait about 10 seconds, then confirm it's healthy:

```powershell
docker compose ps
```

Status should show `healthy` or `Up`.

---

## Step 6 — Decide: Keep Existing Data, or Start Fresh?

**Option A — Keep yesterday's data** (twins, review decisions, rulebook
changes all preserved): skip to Step 8.

**Option B — Clean slate** (recommended if you're about to run a demo and
want predictable, repeatable results):

```powershell
docker compose down -v
docker compose up -d
```

Wait ~10 seconds after `up -d`, then continue to Step 7.

---

## Step 7 — Initialize and Seed the Database (only if you chose Option B)

```powershell
python scripts/init_db.py
python scripts/seed_data.py
```

Expected output:
```
All tables created (or already existed).
Seeded 60 new patients (60 total in file).
Seeded initial rulebook.
```

> **Note:** since new columns (`rag_details`, `stage_durations_ms`) were
> added to the twins table for the Governance page, if you're on old data
> from before that change and hit a database error, do a full reset:
> `docker compose down -v && docker compose up -d` then re-run this step.

---

## Step 8 — Confirm Your `.env` File Has Everything It Needs

Open `.env` (not `.env.example`) and confirm these are all set with real
values, not placeholders:

```
DATABASE_URL=postgresql://trust_fabric:trust_fabric_dev_password@localhost:5432/trust_fabric
OPENROUTER_API_KEY=sk-or-...
EXPLAINABILITY_MODEL=openai/gpt-oss-20b:free
FALLBACK_EXPLAINABILITY_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
GROQ_API_KEY=gsk-...
CHAT_ASSISTANT_MODEL=openai/gpt-oss-120b
CORS_ALLOWED_ORIGIN=http://localhost:5173
```

---

## Step 9 — Start the Backend

```powershell
uvicorn backend.main:app --reload --port 8000
```

**Watch for this exact sequence** — if any line is missing or shows an
error, stop here and fix it before moving on:

```
INFO:backend.main:Database connection verified.
INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer: all-MiniLM-L6-v2
INFO:backend.main:RAG knowledge base loaded.
INFO:apscheduler.scheduler:Scheduler started
INFO:backend.main:Trust Monitoring scheduler started (every 6.0 hours).
INFO:     Application startup complete.
```

Leave this terminal running. Quick health check in a browser:
`http://localhost:8000/health` → should return `{"status":"ok"}`

---

## Step 10 — Start the Frontend (new terminal)

```powershell
cd C:\Users\Aakash\Documents\trust_fabric\frontend
npm run dev
```

Wait for:
```
➜  Local:   http://localhost:5173/
```

---

## Step 11 — Log In

Go to **http://localhost:5173**

| Username | Password | Role | Use this for |
|---|---|---|---|
| `dr.mitchell` | `clinician123` | Clinician | Read-only Dashboard + Twin Detail view |
| `compliance.lead` | `compliance123` | Compliance/Governance | Everything — Rulebook, Trust Monitoring, Governance, review actions |

Use `compliance.lead` for demos — it's the only role that sees Rulebook
Settings, Trust Monitoring, and the Governance page.

---

## Step 12 — Load Data to Actually Look At

### Option A — Full 10-patient live demo (recommended before showing anyone)

Open the Dashboard first, **then** in a new terminal:

```powershell
cd C:\Users\Aakash\Documents\trust_fabric
venv\Scripts\activate
python scripts/run_demo_10_patients.py
```

Watch the Dashboard's **"Now Processing"** panel track each patient live
through all 4 stages as the script sends them.

### Option B — All 60 seed predictions (slower, more data to browse)

```powershell
python scripts/run_pipeline_on_seed_data.py
```

---

## Step 13 — Verify Everything Actually Works

Quick checklist, in order of what's most likely to have an issue after a
long gap:

- [ ] **Dashboard** — metric cards show non-zero numbers, table has rows
- [ ] **Twin Detail** — click any row, confirm the Explanation card shows real text (not empty)
- [ ] **Governance page** — sidebar → Governance, confirm the table shows per-patient stage timings and an Explainability badge (green = primary model worked)
- [ ] **Trust Monitoring** — charts render, "Run trust check now" button works
- [ ] **Rulebook Settings** — loads current values, Save Changes shows the success toast
- [ ] **Chat Assistant** — click the floating sparkle button (bottom-right), ask *"Why was P0009 flagged?"* — should get a real, grounded answer within a few seconds

If the chatbot is slow or fails on first try, that's usually just the
first Groq call warming up — try again once.

---

## Troubleshooting — Issues You've Hit Before

| Symptom | Cause | Fix |
|---|---|---|
| `psycopg2.OperationalError: password authentication failed` | Native Postgres service running on port 5432 | Go back to Step 3 |
| `netstat` shows two processes on :5432 | Same as above | Stop the native service |
| Script says `FAILED` / `TimeoutError` but Twin Detail shows the right answer anyway | The LLM call was just slow — the script gave up watching, but the backend kept processing in the background | Not a real failure; increase `POLL_TIMEOUT_SECONDS` in the script if this happens often |
| Chat/Explanation shows `"Response too short"` warnings in backend logs repeatedly | `max_tokens` too low for a reasoning model, or Groq/OpenRouter key issue | Confirm `.env` keys are real (Step 8); check backend logs for the actual exception |
| "Now Processing" panel stuck on an old patient while newer ones are clearly running | A very old abandoned request lingering — should self-correct after ~2 minutes (`STALE_AFTER_SECONDS`) | Wait, or restart the backend |
| Database errors mentioning missing columns | Schema changed since your last seed (e.g. Governance page's new fields) | Full reset: `docker compose down -v && docker compose up -d` then Step 7 |

---

## Shutting Down at the End of the Day

```powershell
# Ctrl+C in both the backend and frontend terminals, then:
docker compose down
```

This stops the containers but **keeps your data** (no `-v` flag) — next
time you start up, skip straight to Step 6 → Option A.

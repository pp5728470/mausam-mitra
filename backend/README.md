# Mausam Mitra Backend

FastAPI + SQLAlchemy 2 + PostgreSQL/PostGIS foundation for the Mausam Mitra weather intelligence platform.

> **Demo data:** Seeded incidents and reports are **SIMULATED** operating-picture records aligned with the Phase 2 frontend mocks. They are **not** live weather observations.

## Requirements

- Python **3.11+** (3.12+ preferred)
- Docker / Docker Compose (PostGIS)
- PostgreSQL client tools optional

## Layout

```
backend/
├── app/
│   ├── api/          # FastAPI routers (/api/v1)
│   ├── core/         # Settings + enums
│   ├── db/           # Session, seed
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic v2 schemas
│   ├── services/     # Business logic
│   └── main.py
├── alembic/
├── tests/
├── requirements.txt
├── .env.example
└── Dockerfile
```

The Next.js frontend remains at the **repository root** (not moved into `/frontend`).

## 1. Environment setup

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
```

Edit `.env` if needed. Defaults match `docker-compose.yml` at the repo root.

## 2. Start PostgreSQL (PostGIS)

From the **repository root**:

```bash
docker compose up -d
```

Wait until healthy:

```bash
docker compose ps
```

## 3. Run migrations

```bash
cd backend
alembic upgrade head
```

This creates the `postgis` extension, `incidents`, and `reports` tables plus indexes.

## 4. Seed demo data

```bash
python -m app.db.seed
```

Loads **12** simulated incidents (same locations as the frontend mock set) plus associated demo reports.

## 5. Start FastAPI

```bash
# Preferred (cross-platform). On Windows this uses SelectorEventLoop for psycopg async.
python run.py

# Equivalent CLI form (custom loop required on Windows):
uvicorn app.main:app --port 8000 --loop app.loop:selector_loop_factory

# Linux/macOS only (default uvicorn asyncio/Proactor path is fine there):
uvicorn app.main:app --reload --port 8000
```

- Health: http://localhost:8000/api/v1/health  
- Swagger: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

## 6. Useful API examples

```bash
curl http://localhost:8000/api/v1/health

curl "http://localhost:8000/api/v1/incidents?severity=HIGH&limit=20"

curl "http://localhost:8000/api/v1/incidents/nearby?latitude=18.52&longitude=73.85&radius_km=100"
```

## 7. Tests

With Postgres running and migrations applied:

```bash
cd backend
pytest -q
```

## CORS

Configured via `CORS_ORIGINS` (comma-separated). Default: `http://localhost:3000`.  
Do **not** use `allow_origins=["*"]` for normal development.

## Frontend note

The Next.js app continues to use **mock incidents** for the Command Center UI.  
Typed API clients under `src/lib/api/` can call this backend; Phase 4 can switch mock → API without redesigning components.

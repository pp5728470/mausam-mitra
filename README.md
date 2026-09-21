# Mausam Mitra

National Weather Intelligence platform (SIH 2026 prototype).

## Structure

| Path | Role |
|------|------|
| Repository root | Next.js frontend (Phases 1–2 Command Center) |
| `backend/` | FastAPI + PostgreSQL/PostGIS API (Phase 3) |
| `docker-compose.yml` | Local PostGIS database |

The frontend **was not moved** into `/frontend` — it remains at the repo root.

## Frontend

```bash
npm install
npm run dev
```

Open http://localhost:3000 — Command Center uses **simulated mock incidents** until Phase 4 API switchover.

## Backend

See [`backend/README.md`](backend/README.md) for full setup.

Quick start (Docker Desktop must be running):

```bash
docker compose up -d
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

> **Port note:** Compose publishes PostGIS on host **5433** (container 5432) so it does not collide with a local Windows PostgreSQL on `127.0.0.1:5432`. `DATABASE_URL` in `backend/.env.example` matches.
- Health: http://localhost:8000/api/v1/health  
- Swagger: http://localhost:8000/docs  

Seeded DB records are **SIMULATED demo intelligence**, not live weather.

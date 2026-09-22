# Mausam Mitra — Smart India Hackathon (SIH) Demo Guide

> **Tagline:** Turning scattered weather signals into verified, actionable intelligence.  
> **Core Definition:** A weather incident intelligence and decision-support platform that transforms fragmented weather-related signals into evidence-backed, correlated incidents for authorized disaster-management teams.

---

## 1. Executive Summary & Value Proposition

During severe weather anomalies (cloudbursts, urban flash floods, dense fog corridors, gale storms), emergency responders and municipal corporations face two major problems:
1. **Signal Fragmentation:** Citizen distress calls, sensor feeds, and weather alerts arrive across disjoint channels without spatial-temporal grouping.
2. **Action Paralysis:** Raw data contains noise, duplicates, and uncorroborated reports, making it hard to prioritize limited emergency assets.

**Mausam Mitra** solves this with an **automated Spatio-Temporal Correlation Engine** paired with **Human-in-the-Loop Verification** and **Role-Based Alert Escalation**.

---

## 2. Real Architecture vs. Demo Boundaries

Judges respect systems with clearly delineated production capabilities vs. demo fallbacks. Mausam Mitra maintains absolute architectural honesty:

| Feature / Subsystem | Status in Demo | Technical Implementation |
| :--- | :--- | :--- |
| **User Authentication & RBAC** | **Real / Production-Grade** | FastAPI JWT auth with `ADMIN`, `ANALYST`, `VERIFIER`, `CITIZEN` roles; Argon2 password hashing. |
| **Database & Persistence** | **Real / Production-Grade** | PostgreSQL with SQLAlchemy 2.0 async sessions, foreign key cascades, migration tracking. |
| **Spatio-Temporal Correlation** | **Real Algorithm** | PostGIS-based spatio-temporal correlation using configurable geographic radius and temporal windows (`backend/app/services/correlation_engine.py`). |
| **Alert Engine & Deduplication** | **Real / Production-Grade** | Database deduplication via unique constraint `dedupe_key` with nested savepoints and scope-based dispatch. |
| **Weather Ingestion** | **Integration Ready** | OpenWeatherMap integration ready (`backend/app/services/weather_provider.py` & `weather_ingestion.py`). Station telemetry gathers when active incidents trigger spatial-temporal evidence collection. (Note: The `weather_observations` table starts empty until external weather feeds are polled). |
| **Interactive GIS Map** | **Resilient Fallback** | MapLibre GL with live incident markers; includes an embedded local GeoJSON vector basemap fallback when external map tiles are unreachable. |
| **Offline / Resilient Fallbacks** | **Implemented Fallbacks** | Frontend provides transparent demo/mock fallback when backend connectivity is unavailable, allowing uninterrupted demonstration. |
| **Live Activity Feed** | **Simulated for Demo** | Visual event ticker labeled `DEMO ACTIVITY` in the UI to provide a deterministic demonstration of incident stream telemetry. |

---

## 3. Demo Setup & Deterministic Seeding

To ensure a 100% reliable, zero-surprise live demonstration, Mausam Mitra includes an idempotent database seed script.

### Step 1: Start Backend & Frontend
```bash
# Terminal 1 (Backend):
cd backend
.\.venv\Scripts\activate   # (or source .venv/bin/activate on Linux/macOS)
uvicorn app.main:app --reload --port 8000

# Terminal 2 (Frontend):
npm run dev
```

### Step 2: Seed Deterministic Maharashtra Demo Data
```bash
cd backend
python -m app.scripts.seed_demo
```
*Note: This script is fully idempotent (`INSERT ... ON CONFLICT DO UPDATE`). It creates 4 user accounts, 5 correlated Maharashtra incidents, 17 linked citizen reports, timeline audit events, and scoped alerts.*

---

## 4. Demo Credentials (Development Database Only)

| Role | Email | Password | Primary Purpose in Demo |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@mausam.demo` | `Demo@Admin1` | Full system oversight, incident escalation, administrative alert broadcast. |
| **Analyst** | `analyst@mausam.demo` | `Demo@Analyst1` | Command Center operations, spatial correlation review, analytics intelligence. |
| **Verifier** | `verifier@mausam.demo` | `Demo@Verify1` | Verification queue, field report validation/rejection, ground-truth tagging. |
| **Citizen Reporter** | `citizen@mausam.demo` | `Demo@Citizen1` | Public reporting portal (`/reports`), submission of distress/observation reports. |

---

## 5. Live Presentation Script (5–7 Minute Flow)

### Act I: The Operational Picture (Analyst View — 2 mins)
1. **Navigate to:** `http://localhost:3000/login`
2. **Log in as:** `analyst@mausam.demo` / `Demo@Analyst1`
3. **Show Command Center (`/overview`):**
   - Point out the **Interactive Map** centered over Maharashtra with color-coded incident clusters.
   - Point out the **Data Source Indicator:** Notice the system displays `SYSTEM LIVE` with real-time API connectivity to FastAPI.
   - Highlight the **Correlated Incident Card**: `[MM-DEMO-WKWL] Wakad / Hinjewadi Waterlogging`.
   - Explain the correlation metrics: **Evidence Score (87/100)**, **5 linked citizen reports**, **6.2 km cluster radius**, **90-minute sliding window**.
   - Emphasize to judges: *"The system didn't just log 5 separate complaints. It correlated them into a single actionable incident with high confidence. Correlation scores represent spatial-temporal signal corroboration, not a weather forecast or truth claim."*

### Act II: Incident Audit & Timeline (1.5 mins)
1. **Click on the Wakad incident** to open its detail view:
   - Walk through the **Timeline**: Initial citizen report → cluster formation → alert escalation.
   - Show the **Linked Signals / Reports list**: Reports from Wakad bridge, Hinjewadi Phase 1, and Tathawade underpass, showing individual severity and notes.
   - Show the **Spatial-Temporal Cluster Boundary**: Explain how PostGIS spatial indexing (`ST_DWithin`) bounds the cluster and rejects distant or stale signals.

### Act III: Verification & Field Trust (Verifier View — 1.5 mins)
1. **Switch user / Open incognito window:** Log in as `verifier@mausam.demo` / `Demo@Verify1`.
2. **Navigate to:** `/verification` (Verification Queue):
   - Show pending unverified citizen reports requiring human confirmation.
   - Emphasize to judges: *"Mausam Mitra never treats raw citizen reports or algorithm scores as unassailable truth. Verification is strictly human-in-the-loop."*
   - Click **Verify** or **Reject** on a report with an audit remark (e.g., *"Confirmed via municipal traffic camera"*).
   - Show that verification status updates in real-time and recalculates incident evidence strength.

### Act IV: Alerts & Decision Support (1 min)
1. **Navigate to:** `/notifications` (Alert Centre):
   - Show role-scoped alerts:
     - Verifiers only receive `VERIFICATION_REQUIRED` alerts.
     - Analysts receive `INCIDENT_CREATED` and `INCIDENT_TREND_CHANGED`.
     - Admins receive critical `INCIDENT_ESCALATED` alerts.
   - Demonstrate **Mark as Read** and **Acknowledge** actions with instantaneous visual updates.

### Act V: Analytics & Intelligence (1 min)
1. **Navigate to:** `/analytics`:
   - Point out the **Overview KPIs**: Total Reports, Active Incidents, Average Resolution Time, Evidence Ratio.
   - Highlight the **Geographic Concentration** card: Displays top spatial clusters with resolved corridor names (*Wakad / Hinjewadi, Pune*, *Shivajinagar*, *Bandra / Kurla, Mumbai*) rather than raw coordinates.
   - Highlight the **Classification Intelligence** and **Severity Breakdown**.

---

## 6. Key Talking Points for Judging Inquiries

### Q: "How do you prevent malicious or fake reports?"
> *"Mausam Mitra uses a defense-in-depth model:
> 1. Citizen reports do not automatically become active incidents. They are ingested as raw candidate signals.
> 2. An incident is only spawned or correlated when multiple independent reports align within a strict spatio-temporal boundary (e.g., within 5 km and 90 minutes).
> 3. Reports pass through the Human-in-the-Loop Verifier queue where authorized personnel validate evidence before incident status elevates to HIGH/CRITICAL."*

### Q: "What if there is no internet connection in a disaster zone?"
> *"The frontend is engineered with resilient fallbacks:
> 1. MapLibre GL includes an embedded local GeoJSON outline of India so the map interface remains functional even if external tile servers are unreachable.
> 2. The Command Center supports a transparent demo/mock fallback when backend connectivity is unavailable."*

### Q: "How does this integrate with official meteorological agencies like IMD?"
> *"Phase 8 incorporates a pluggable weather provider adapter (OpenWeatherMap integration ready); the adapter architecture allows drop-in connection to IMD or state disaster management authority (SDMA) APIs."*

---

## 7. SIH Presentation Checklist

- [ ] FastAPI backend running on port 8000 (`uvicorn app.main:app --port 8000`)
- [ ] Next.js frontend running on port 3000 (`npm run dev`)
- [ ] PostgreSQL running on port 5433 (via Docker or local service)
- [ ] Executed `python -m app.scripts.seed_demo` (upserts 4 users, 5 incidents, 17 reports, 15 alerts)
- [ ] Verified demo login with `analyst@mausam.demo` / `Demo@Analyst1`
- [ ] Verified `/overview` displays interactive map and live Maharashtra clusters
- [ ] Verified `/notifications` displays sidebar and loads alerts cleanly
- [ ] Verified `/analytics` displays metrics and geographic concentration cards cleanly
- [ ] Verified citizen reporting portal is accessible at `/reports`

import asyncio
import os
import json
from datetime import datetime

# Enforce dev DB URL
os.environ["DATABASE_URL"] = "postgresql+psycopg://mausam:mausam_dev_password@localhost:5433/mausam_mitra"

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    
    async with engine.connect() as conn:
        # Get counts
        res = await conn.execute(text("SELECT COUNT(*) FROM reports;"))
        total_reports = res.scalar()
        
        res = await conn.execute(text("SELECT origin, COUNT(*) FROM incidents GROUP BY origin;"))
        incident_counts = {row[0]: row[1] for row in res.fetchall()}
        
        # Get MANUAL candidates
        query = text("""
            SELECT id, incident_code, origin, created_at, updated_at, title, description
            FROM incidents 
            WHERE origin = 'MANUAL'
        """)
        res = await conn.execute(query)
        manual_incidents = []
        for row in res.fetchall():
            inc_id = row[0]
            rep_count_res = await conn.execute(text("SELECT COUNT(*) FROM reports WHERE incident_id = :iid"), {"iid": inc_id})
            rep_count = rep_count_res.scalar()
            
            manual_incidents.append({
                "id": str(inc_id),
                "code": row[1],
                "origin": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "updated_at": row[4].isoformat() if row[4] else None,
                "title": row[5],
                "description": row[6],
                "linked_reports": rep_count
            })
            
    with open("backend/scripts/dev_db_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_reports": total_reports,
            "incident_counts": incident_counts,
            "manual_incidents": manual_incidents
        }, f, indent=2)
    
    await engine.dispose()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

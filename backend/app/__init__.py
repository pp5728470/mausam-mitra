"""Mausam Mitra FastAPI application package."""

import asyncio
import sys

# psycopg async requires SelectorEventLoop on Windows (not ProactorEventLoop).
# Prefer `python run.py` so the policy is set before uvicorn creates the loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

"""
Windows-safe FastAPI launcher.

psycopg async cannot use ProactorEventLoop; set Selector policy before uvicorn
creates the event loop (importing app.main alone is too late under uvicorn CLI).
"""

from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        # uvicorn's built-in "asyncio" factory forces ProactorEventLoop on Windows,
        # which breaks psycopg async — use Selector instead.
        loop="app.loop:selector_loop_factory",
    )


if __name__ == "__main__":
    main()

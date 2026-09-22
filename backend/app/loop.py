"""Uvicorn custom loop factory — SelectorEventLoop for psycopg async on Windows."""

from __future__ import annotations

import asyncio


def selector_loop_factory() -> asyncio.AbstractEventLoop:
    """Return a SelectorEventLoop (required by psycopg async; uvicorn defaults to Proactor on Win32)."""
    return asyncio.SelectorEventLoop()

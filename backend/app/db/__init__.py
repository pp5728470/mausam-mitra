"""Database package — import models here so Alembic can discover metadata."""

from app.db.base import Base
from app.models.incident import Incident
from app.models.report import Report

__all__ = ["Base", "Incident", "Report"]

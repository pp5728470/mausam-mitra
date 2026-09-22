"""Deterministic evidence evaluation for report verification (Phase 6).

Providers return explainable factors. Scores are not truth claims.
Unavailable evidence is omitted from the overall average (never treated as 0).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    EvidenceType,
    SourceType,
    VerificationRecommendation,
    VerificationStatus,
)
from app.models.evidence import ReportEvidence
from app.models.report import Report
from app.models.weather import WeatherObservation
from app.core.config import settings

NEARBY_RADIUS_M = 2500.0
NEARBY_TIME_WINDOW = timedelta(hours=6)
DUPLICATE_LOOKBACK = timedelta(hours=24)
DUPLICATE_RADIUS_M = 5000.0

# Removed DEMO_WEATHER_CONTEXT


@dataclass
class EvidenceFactor:
    evidence_type: EvidenceType
    title: str
    description: str
    score: float | None
    confidence: float | None
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    available: bool = True


@dataclass
class EvidenceEvaluationResult:
    factors: list[EvidenceFactor]
    evidence_score: float | None
    evidence_coverage: str
    available_count: int
    total_signals: int
    verification_recommendation: VerificationRecommendation


class EvidenceProvider(ABC):
    @abstractmethod
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        raise NotImplementedError


def _normalize_text(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _token_jaccard(a: str, b: str) -> float:
    ta = set(_normalize_text(a).split())
    tb = set(_normalize_text(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _category_keywords(report: Report) -> set[str]:
    blob = f"{report.classification or ''} {report.title} {report.description or ''}".lower()
    keys = set()
    for word in (
        "flood",
        "waterlog",
        "rain",
        "heat",
        "storm",
        "wind",
        "lightning",
        "hail",
        "landslide",
        "fog",
        "visibility",
    ):
        if word in blob:
            keys.add(word)
    return keys


class LocationEvidenceProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        from geoalchemy2 import Geography

        origin_geog = func.ST_SetSRID(
            ST_MakePoint(report.longitude, report.latitude), 4326
        ).cast(Geography)
        report_geog = Report.location.cast(Geography)

        stmt = (
            select(func.count())
            .select_from(Report)
            .where(
                Report.id != report.id,
                ST_DWithin(report_geog, origin_geog, NEARBY_RADIUS_M),
            )
        )
        count = int((await session.execute(stmt)).scalar_one() or 0)

        if count == 0:
            return EvidenceFactor(
                evidence_type=EvidenceType.LOCATION_CONSISTENCY,
                title="Location consistency",
                description="No nearby corroborating reports currently available.",
                score=None,
                confidence=None,
                source="postgis",
                metadata={"nearby_count": 0, "radius_m": NEARBY_RADIUS_M},
                available=False,
            )

        score = min(95.0, 55.0 + count * 8.0)
        confidence = min(95.0, 60.0 + count * 6.0)
        return EvidenceFactor(
            evidence_type=EvidenceType.LOCATION_CONSISTENCY,
            title="Location consistency",
            description=(
                f"Multiple related reports were submitted within the surrounding area "
                f"({count} within {NEARBY_RADIUS_M / 1000:.1f} km)."
            ),
            score=round(score, 1),
            confidence=round(confidence, 1),
            source="postgis",
            metadata={"nearby_count": count, "radius_m": NEARBY_RADIUS_M},
            available=True,
        )


class TimeEvidenceProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        reported = report.reported_at
        received = report.received_at
        if reported is None:
            return EvidenceFactor(
                evidence_type=EvidenceType.TIME_CONSISTENCY,
                title="Time consistency",
                description="No client-reported timestamp provided; using receive time only.",
                score=70.0,
                confidence=55.0,
                source="timestamps",
                metadata={"reported_at": None},
                available=True,
            )

        # Normalize aware datetimes
        if reported.tzinfo is None:
            reported = reported.replace(tzinfo=timezone.utc)
        if received.tzinfo is None:
            received = received.replace(tzinfo=timezone.utc)

        delta = abs((received - reported).total_seconds())
        hours = delta / 3600.0

        if hours <= 2:
            score, confidence = 94.0, 90.0
            desc = "Report timing is consistent with receipt time."
        elif hours <= 12:
            score, confidence = 78.0, 75.0
            desc = "Moderate delay between reported event time and receipt; timing is plausible."
        elif hours <= 48:
            score, confidence = 55.0, 60.0
            desc = "Timestamp requires review — notable gap between reported and received times."
        else:
            score, confidence = 35.0, 50.0
            desc = "Timestamp requires review — large gap between reported and received times."

        return EvidenceFactor(
            evidence_type=EvidenceType.TIME_CONSISTENCY,
            title="Time consistency",
            description=desc,
            score=score,
            confidence=confidence,
            source="timestamps",
            metadata={
                "delta_seconds": int(delta),
                "reported_at": reported.isoformat(),
                "received_at": received.isoformat(),
            },
            available=True,
        )


class WeatherCorrelationProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        from geoalchemy2 import Geography

        keys = _category_keywords(report)
        if not keys:
            return EvidenceFactor(
                evidence_type=EvidenceType.WEATHER_CORRELATION,
                title="Weather correlation",
                description="Report category does not require weather correlation.",
                score=None,
                confidence=None,
                source="weather_observation",
                metadata={"live_weather": False},
                available=False,
            )

        origin_geog = func.ST_SetSRID(
            ST_MakePoint(report.longitude, report.latitude), 4326
        ).cast(Geography)
        
        radius_m = settings.weather_evidence_radius_km * 1000.0
        time_window = timedelta(minutes=settings.weather_evidence_time_window_minutes)

        window_start = report.received_at - time_window
        window_end = report.received_at + time_window
        
        if report.received_at.tzinfo is None:
            window_start = report.received_at.replace(tzinfo=timezone.utc) - time_window
            window_end = report.received_at.replace(tzinfo=timezone.utc) + time_window

        distance_m = ST_Distance(WeatherObservation.location.cast(Geography), origin_geog)

        stmt = (
            select(WeatherObservation, distance_m.label("distance_m"))
            .where(
                ST_DWithin(WeatherObservation.location.cast(Geography), origin_geog, radius_m),
                WeatherObservation.observed_at >= window_start,
                WeatherObservation.observed_at <= window_end,
            )
            .order_by(distance_m.asc())
            .limit(1)
        )
        
        result = await session.execute(stmt)
        row = result.first()
        
        if not row:
            return EvidenceFactor(
                evidence_type=EvidenceType.WEATHER_CORRELATION,
                title="Weather correlation",
                description="No nearby weather observations available for the report's time and location.",
                score=None,
                confidence=None,
                source="weather_observation",
                metadata={"live_weather": False, "status": "UNAVAILABLE"},
                available=False,
            )
            
        obs, dist = row
        obs: WeatherObservation
        
        # Calculate time diff
        obs_time = obs.observed_at
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)
        rep_time = report.received_at
        if rep_time.tzinfo is None:
            rep_time = rep_time.replace(tzinfo=timezone.utc)
        time_diff_min = int(abs((obs_time - rep_time).total_seconds()) / 60)

        # Correlation logic
        score = None
        desc = ""
        matched = False
        
        if "flood" in keys or "waterlog" in keys or "rain" in keys:
            if obs.precipitation_mm is not None:
                if obs.precipitation_mm > 5.0:
                    score = 92.0
                    desc = f"Heavy precipitation ({obs.precipitation_mm}mm) recorded nearby."
                    matched = True
                elif obs.precipitation_mm > 0.0:
                    score = 75.0
                    desc = f"Light/Moderate precipitation ({obs.precipitation_mm}mm) recorded nearby."
                    matched = True
                else:
                    score = 30.0
                    desc = "No precipitation recorded nearby during this time."
                    matched = True
        
        if not matched and ("storm" in keys or "wind" in keys):
            if obs.wind_speed is not None:
                if obs.wind_speed > 15.0:
                    score = 92.0
                    desc = f"Strong winds ({obs.wind_speed} m/s) recorded nearby."
                    matched = True
                elif obs.wind_speed > 8.0:
                    score = 75.0
                    desc = f"Moderate winds ({obs.wind_speed} m/s) recorded nearby."
                    matched = True
                else:
                    score = 30.0
                    desc = f"Only light winds ({obs.wind_speed} m/s) recorded nearby."
                    matched = True
                    
        if not matched and "heat" in keys:
            if obs.temperature is not None:
                if obs.temperature >= 38.0:
                    score = 94.0
                    desc = f"Extreme heat ({obs.temperature}°C) recorded nearby."
                    matched = True
                elif obs.temperature >= 32.0:
                    score = 75.0
                    desc = f"High temperatures ({obs.temperature}°C) recorded nearby."
                    matched = True
                else:
                    score = 25.0
                    desc = f"Normal temperatures ({obs.temperature}°C) recorded nearby."
                    matched = True
                    
        if not matched and ("fog" in keys or "visibility" in keys):
            if obs.visibility is not None:
                if obs.visibility <= 1000:
                    score = 92.0
                    desc = f"Low visibility ({obs.visibility}m) recorded nearby."
                    matched = True
                elif obs.visibility <= 4000:
                    score = 70.0
                    desc = f"Moderate visibility ({obs.visibility}m) recorded nearby."
                    matched = True
                else:
                    score = 30.0
                    desc = f"Clear visibility ({obs.visibility}m) recorded nearby."
                    matched = True

        if not matched:
            return EvidenceFactor(
                evidence_type=EvidenceType.WEATHER_CORRELATION,
                title="Weather correlation",
                description="Weather data available, but lacks specific measurements to verify this category.",
                score=None,
                confidence=None,
                source="weather_observation",
                metadata={"live_weather": True, "provider": obs.provider, "status": "UNAVAILABLE"},
                available=False,
            )

        full_desc = (
            f"LIVE Weather Observation: {desc} "
            f"(Distance: {dist / 1000.0:.1f} km, Time difference: {time_diff_min} min, "
            f"Provider: {obs.provider})"
        )

        return EvidenceFactor(
            evidence_type=EvidenceType.WEATHER_CORRELATION,
            title="Weather correlation",
            description=full_desc,
            score=score,
            confidence=85.0,
            source="weather_observation",
            metadata={
                "live_weather": True,
                "provider": obs.provider,
                "distance_km": round(dist / 1000.0, 2),
                "time_difference_minutes": time_diff_min,
                "weather_condition": obs.weather_condition,
                "rainfall": obs.precipitation_mm,
                "wind_speed": obs.wind_speed,
                "temperature": obs.temperature,
                "explanation": desc,
            },
            available=True,
        )


class NearbyReportsProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        from geoalchemy2 import Geography

        origin_geog = func.ST_SetSRID(
            ST_MakePoint(report.longitude, report.latitude), 4326
        ).cast(Geography)
        report_geog = Report.location.cast(Geography)
        distance_m = ST_Distance(report_geog, origin_geog)

        window_start = report.received_at - NEARBY_TIME_WINDOW
        if report.received_at.tzinfo is None:
            window_start = report.received_at.replace(tzinfo=timezone.utc) - NEARBY_TIME_WINDOW

        stmt = (
            select(Report.id, distance_m.label("distance_m"), Report.classification)
            .where(
                Report.id != report.id,
                ST_DWithin(report_geog, origin_geog, NEARBY_RADIUS_M),
                Report.received_at >= window_start,
            )
            .order_by(distance_m.asc())
            .limit(50)
        )
        rows = (await session.execute(stmt)).all()
        count = len(rows)
        keys = _category_keywords(report)
        related = 0
        max_dist = 0.0
        for _id, dist, classification in rows:
            other_keys = set()
            blob = (classification or "").lower()
            for word in keys:
                if word in blob:
                    other_keys.add(word)
            if not keys or other_keys or classification is None:
                related += 1
            if dist is not None:
                max_dist = max(max_dist, float(dist))

        if related == 0:
            return EvidenceFactor(
                evidence_type=EvidenceType.NEARBY_REPORTS,
                title="Nearby reports",
                description="No related reports within the spatial/time window.",
                score=None,
                confidence=None,
                source="postgis",
                metadata={
                    "related_count": 0,
                    "radius_m": NEARBY_RADIUS_M,
                    "window_hours": NEARBY_TIME_WINDOW.total_seconds() / 3600,
                },
                available=False,
            )

        score = min(94.0, 50.0 + related * 9.0)
        confidence = min(92.0, 58.0 + related * 7.0)
        km = NEARBY_RADIUS_M / 1000.0
        return EvidenceFactor(
            evidence_type=EvidenceType.NEARBY_REPORTS,
            title="Nearby reports",
            description=f"{related} related reports within {km:.1f} km.",
            score=round(score, 1),
            confidence=round(confidence, 1),
            source="postgis",
            metadata={
                "related_count": related,
                "candidate_count": count,
                "radius_m": NEARBY_RADIUS_M,
                "max_distance_m": round(max_dist, 1),
            },
            available=True,
        )


class MediaEvidenceProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        if not report.media_url:
            return EvidenceFactor(
                evidence_type=EvidenceType.MEDIA_EVIDENCE,
                title="Media evidence",
                description="No media evidence submitted.",
                score=None,
                confidence=None,
                source="media_metadata",
                metadata={"status": "UNAVAILABLE"},
                available=False,
            )

        url = report.media_url.lower()
        supported = any(
            ext in url for ext in (".jpg", ".jpeg", ".png", ".webp", "demo://local/")
        )
        if supported:
            return EvidenceFactor(
                evidence_type=EvidenceType.MEDIA_EVIDENCE,
                title="Media evidence",
                description="Media attachment available for human review.",
                score=72.0,
                confidence=65.0,
                source="media_metadata",
                metadata={
                    "status": "AVAILABLE",
                    "media_url": report.media_url,
                    "vision": False,
                },
                available=True,
            )

        return EvidenceFactor(
            evidence_type=EvidenceType.MEDIA_EVIDENCE,
            title="Media evidence",
            description="Media reference present but format needs review.",
            score=50.0,
            confidence=45.0,
            source="media_metadata",
            metadata={"status": "NEEDS_REVIEW", "media_url": report.media_url},
            available=True,
        )


class DuplicateRiskProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        from geoalchemy2 import Geography

        origin_geog = func.ST_SetSRID(
            ST_MakePoint(report.longitude, report.latitude), 4326
        ).cast(Geography)
        report_geog = Report.location.cast(Geography)
        since = report.received_at - DUPLICATE_LOOKBACK
        if report.received_at.tzinfo is None:
            since = report.received_at.replace(tzinfo=timezone.utc) - DUPLICATE_LOOKBACK

        stmt = (
            select(Report)
            .where(
                Report.id != report.id,
                Report.received_at >= since,
                ST_DWithin(report_geog, origin_geog, DUPLICATE_RADIUS_M),
            )
            .limit(40)
        )
        candidates = list((await session.execute(stmt)).scalars().all())
        best = 0.0
        best_id: str | None = None
        target = f"{report.title} {report.description or ''}"
        for other in candidates:
            sim = _token_jaccard(target, f"{other.title} {other.description or ''}")
            if sim > best:
                best = sim
                best_id = str(other.id)

        if best >= 0.72:
            # High similarity → lower evidence contribution (risk flag), still available.
            return EvidenceFactor(
                evidence_type=EvidenceType.DUPLICATE_RISK,
                title="Duplicate risk",
                description=(
                    "A highly similar report was submitted nearby within the recent "
                    "time window. This is a signal for review, not proof of false reporting."
                ),
                score=28.0,
                confidence=70.0,
                source="text_similarity",
                metadata={
                    "risk": "POTENTIAL_MATCH",
                    "similarity": round(best, 3),
                    "matched_report_id": best_id,
                },
                available=True,
            )

        if best >= 0.45:
            return EvidenceFactor(
                evidence_type=EvidenceType.DUPLICATE_RISK,
                title="Duplicate risk",
                description="Some textual similarity with a recent nearby report; low–moderate review interest.",
                score=62.0,
                confidence=58.0,
                source="text_similarity",
                metadata={
                    "risk": "LOW_MODERATE",
                    "similarity": round(best, 3),
                    "matched_report_id": best_id,
                },
                available=True,
            )

        return EvidenceFactor(
            evidence_type=EvidenceType.DUPLICATE_RISK,
            title="Duplicate risk",
            description="No strong duplicate text signal among recent nearby reports.",
            score=88.0,
            confidence=75.0,
            source="text_similarity",
            metadata={"risk": "LOW", "similarity": round(best, 3)},
            available=True,
        )


class SourceSignalProvider(EvidenceProvider):
    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceFactor:
        if report.source_type == SourceType.OFFICIAL:
            score, confidence = 90.0, 85.0
            desc = "Official / agency source signal strength is high."
        elif report.source_type == SourceType.SENSOR:
            score, confidence = 86.0, 80.0
            desc = "Sensor source signal strength is high."
        elif report.source_type == SourceType.CITIZEN:
            score, confidence = 68.0, 70.0
            desc = "Citizen source signal — useful raw input requiring corroboration."
        else:
            score, confidence = 60.0, 55.0
            desc = "Source signal recorded for review."

        return EvidenceFactor(
            evidence_type=EvidenceType.SOURCE_SIGNAL,
            title="Source signal",
            description=desc,
            score=score,
            confidence=confidence,
            source="source_type",
            metadata={"source_type": report.source_type.value},
            available=True,
        )


def compute_recommendation(
    evidence_score: float | None,
    available_count: int,
) -> VerificationRecommendation:
    if evidence_score is None or available_count < 2:
        return VerificationRecommendation.NEEDS_REVIEW
    if evidence_score >= 85 and available_count >= 4:
        return VerificationRecommendation.HIGH_CONFIDENCE_REVIEW
    if evidence_score >= 70:
        return VerificationRecommendation.CORROBORATED
    return VerificationRecommendation.NEEDS_REVIEW


def aggregate_score(factors: list[EvidenceFactor]) -> tuple[float | None, int, int, str]:
    """Average only available factors with numeric scores — never treat missing as 0."""
    scored = [f for f in factors if f.available and f.score is not None]
    total_signals = len(factors)
    available_count = len(scored)
    if available_count == 0:
        return None, 0, total_signals, f"0 / {total_signals} signals available"
    avg = sum(float(f.score) for f in scored) / available_count  # type: ignore[arg-type]
    coverage = f"{available_count} / {total_signals} signals available"
    return round(avg, 1), available_count, total_signals, coverage


class EvidenceEngine:
    def __init__(self, providers: list[EvidenceProvider] | None = None) -> None:
        self.providers = providers or [
            LocationEvidenceProvider(),
            TimeEvidenceProvider(),
            WeatherCorrelationProvider(),
            NearbyReportsProvider(),
            MediaEvidenceProvider(),
            DuplicateRiskProvider(),
            SourceSignalProvider(),
        ]

    async def evaluate(
        self, session: AsyncSession, report: Report
    ) -> EvidenceEvaluationResult:
        factors: list[EvidenceFactor] = []
        for provider in self.providers:
            factors.append(await provider.evaluate(session, report))

        score, available_count, total_signals, coverage = aggregate_score(factors)
        recommendation = compute_recommendation(score, available_count)
        return EvidenceEvaluationResult(
            factors=factors,
            evidence_score=score,
            evidence_coverage=coverage,
            available_count=available_count,
            total_signals=total_signals,
            verification_recommendation=recommendation,
        )

    async def evaluate_and_persist(
        self, session: AsyncSession, report_id: UUID
    ) -> tuple[Report, EvidenceEvaluationResult]:
        result = await session.execute(
            select(Report)
            .options(selectinload(Report.evidence_items))
            .where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise LookupError("Report not found")

        evaluation = await self.evaluate(session, report)

        # Replace prior evidence rows for this report.
        await session.execute(
            delete(ReportEvidence).where(ReportEvidence.report_id == report.id)
        )

        for factor in evaluation.factors:
            session.add(
                ReportEvidence(
                    report_id=report.id,
                    evidence_type=factor.evidence_type,
                    title=factor.title,
                    description=factor.description,
                    score=factor.score,
                    confidence=factor.confidence,
                    source=factor.source,
                    evidence_metadata={
                        **factor.metadata,
                        "available": factor.available,
                    },
                )
            )

        report.evidence_score = evaluation.evidence_score
        report.verification_recommendation = evaluation.verification_recommendation
        # Do not auto-verify. Optionally mark CORROBORATED recommendation on status.
        if report.verification_status in (
            VerificationStatus.PENDING,
            VerificationStatus.UNDER_REVIEW,
            VerificationStatus.CORROBORATED,
        ):
            if (
                evaluation.verification_recommendation
                == VerificationRecommendation.CORROBORATED
                or evaluation.verification_recommendation
                == VerificationRecommendation.HIGH_CONFIDENCE_REVIEW
            ):
                if report.verification_status != VerificationStatus.VERIFIED:
                    report.verification_status = VerificationStatus.CORROBORATED
            elif (
                evaluation.verification_recommendation
                == VerificationRecommendation.NEEDS_REVIEW
            ):
                if report.verification_status == VerificationStatus.PENDING:
                    report.verification_status = VerificationStatus.UNDER_REVIEW

        await session.commit()
        await session.refresh(report)
        # Reload evidence
        result = await session.execute(
            select(Report)
            .options(selectinload(Report.evidence_items))
            .where(Report.id == report.id)
        )
        report = result.scalar_one()
        return report, evaluation

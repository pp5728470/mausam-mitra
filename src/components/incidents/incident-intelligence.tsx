"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Loader2,
  MapPin,
  Radar,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import { StatusBadge } from "@/components/shared/status-badge";
import {
  ApiError,
  correlateIncidents,
  getIncidentDetail,
  getIncidents,
} from "@/lib/api";
import {
  mapApiIncidentToIncident,
} from "@/lib/api/adapters/incidents";
import type {
  ApiCorrelationFactor,
  ApiIncidentDetail,
  ApiReport,
} from "@/lib/api/types";
import {
  SEVERITY_LABELS,
  STATUS_LABELS,
  trendArrow,
  trendLabel,
} from "@/lib/incidents/utils";
import { rankIncidentQueue } from "@/lib/incidents/metrics";
import { toNullableScore } from "@/lib/verification/format";
import { cn } from "@/lib/utils";
import type { Incident } from "@/types/incident";
import type { OperationalStatus } from "@/types/status";

function formatScore(value: number | null | undefined): string {
  const n = toNullableScore(value);
  if (n === null) return "—";
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

function factorLabel(name: string): string {
  switch (name) {
    case "spatial":
      return "Spatial proximity";
    case "temporal":
      return "Temporal proximity";
    case "category":
      return "Event compatibility";
    case "evidence":
      return "Evidence / verification support";
    case "density":
      return "Report density";
    case "duplicate":
      return "Independent vs duplicate signals";
    default:
      return name;
  }
}

export function IncidentIntelligence() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedIdState] = useState<string | null>(null);
  const [detail, setDetail] = useState<ApiIncidentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isCorrelating, setIsCorrelating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [token, setToken] = useState(0);

  const setSelectedId = (id: string | null) => {
    setSelectedIdState(id);
    setDetail(null);
    if (id) setIsDetailLoading(true);
  };

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const page = await getIncidents(
          { limit: 100, offset: 0 },
          { signal: controller.signal },
        );
        if (controller.signal.aborted) return;
        const items = rankIncidentQueue(
          page.items.map(mapApiIncidentToIncident),
        );
        setIncidents(items);
        setSelectedIdState((current) => {
          if (current && items.some((i) => i.id === current)) return current;
          const preferred =
            items.find((i) => i.isCorrelated)?.id ?? items[0]?.id ?? null;
          if (preferred) setIsDetailLoading(true);
          return preferred;
        });
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof ApiError
            ? err.message
            : "Unable to load incident intelligence.",
        );
        setIncidents([]);
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    })();
    return () => controller.abort();
  }, [token]);

  useEffect(() => {
    if (!selectedId) return;
    const controller = new AbortController();
    void (async () => {
      try {
        const body = await getIncidentDetail(selectedId);
        if (controller.signal.aborted) return;
        setDetail(body);
      } catch {
        if (!controller.signal.aborted) setDetail(null);
      } finally {
        if (!controller.signal.aborted) setIsDetailLoading(false);
      }
    })();
    return () => controller.abort();
  }, [selectedId]);

  const selected = useMemo(
    () => incidents.find((i) => i.id === selectedId) ?? null,
    [incidents, selectedId],
  );

  const runCorrelate = async () => {
    if (!selected) return;
    setIsCorrelating(true);
    setActionMsg(null);
    try {
      const result = await correlateIncidents({
        latitude: selected.coordinates.lat,
        longitude: selected.coordinates.lng,
        radius_km: selected.radiusKm ?? 5,
        window_minutes: selected.timeWindowMinutes ?? 90,
        create_incident: true,
      });
      setActionMsg(result.message);
      setToken((n) => n + 1);
      if (result.incident?.id) setSelectedId(result.incident.id);
    } catch (err) {
      setActionMsg(
        err instanceof ApiError ? err.message : "Correlation request failed.",
      );
    } finally {
      setIsCorrelating(false);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-5">
      <header className="rounded-xl bg-surface/80 px-4 py-5 ring-1 ring-white/6 sm:px-6">
        <p className="text-label text-weather-secondary">Incident intelligence</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Correlated Weather Incidents
        </h1>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          Incidents are formed from correlated weather signals. Correlation
          strength is not a truth claim. Human verification remains separate.
        </p>
      </header>

      {error ? (
        <p className="rounded-lg border border-critical/25 bg-critical/10 px-3 py-2 text-sm">
          {error}
        </p>
      ) : null}
      {actionMsg ? (
        <p className="rounded-lg border border-weather/20 bg-weather/8 px-3 py-2 text-sm">
          {actionMsg}
        </p>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)]">
        <section className="rounded-xl bg-card/60 px-3 py-3 ring-1 ring-white/6">
          <div className="mb-2 flex items-center justify-between gap-2 px-1">
            <h2 className="text-section-title">Incident queue</h2>
            <button
              type="button"
              onClick={() => {
                setIsLoading(true);
                setToken((n) => n + 1);
              }}
              className="inline-flex items-center gap-1 rounded-full border border-white/10 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground"
            >
              <RefreshCw className={cn("size-3", isLoading && "animate-spin")} />
              REFRESH
            </button>
          </div>
          <ul className="max-h-[42rem] space-y-2 overflow-y-auto pr-1">
            {incidents.map((incident) => (
              <li key={incident.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(incident.id)}
                  className={cn(
                    "w-full rounded-lg px-3 py-2.5 text-left transition",
                    selectedId === incident.id
                      ? "bg-weather/12 ring-1 ring-weather/30"
                      : "bg-white/3 hover:bg-white/5",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {incident.code}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {!incident.isCorrelated ? (
                        <span className="rounded border border-white/10 px-1.5 py-0.5 text-[9px] font-semibold tracking-[0.08em] text-muted-foreground">
                          {incident.origin === "manual" ? "MANUAL" : "SEEDED"}
                        </span>
                      ) : null}
                      {incident.isCorrelated ? (
                        <StatusBadge
                          status={incident.status as OperationalStatus}
                        />
                      ) : (
                        <span className="text-[10px] text-muted-foreground">
                          Legacy
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="mt-1 text-sm font-medium text-foreground">
                    {incident.title}
                  </p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    {incident.isCorrelated
                      ? `${SEVERITY_LABELS[incident.severity]} · ${incident.evidence.reportCount} reports · ${trendArrow(incident.trend)} ${trendLabel(incident.trend)}`
                      : `${incident.linkedReportCount} linked reports · no correlation metadata`}
                  </p>
                </button>
              </li>
            ))}
            {!isLoading && incidents.length === 0 ? (
              <li className="px-2 py-6 text-sm text-muted-foreground">
                No correlated incidents available.
              </li>
            ) : null}
          </ul>
        </section>

        <section className="rounded-xl bg-card/60 px-4 py-4 ring-1 ring-white/6 sm:px-5">
          {!selected ? (
            <p className="text-sm text-muted-foreground">
              Select an incident to inspect correlation intelligence.
            </p>
          ) : (
            <div className="space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-mono text-[11px] text-weather-secondary">
                    {selected.code}
                  </p>
                  <h2 className="mt-1 text-xl font-semibold text-foreground">
                    {selected.title}
                  </h2>
                  <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
                    <MapPin className="size-3.5" />
                    {selected.locationLabel}
                  </p>
                  {!selected.isCorrelated ? (
                    <p className="mt-2 rounded-md border border-warning/20 bg-warning/8 px-2 py-1 text-xs text-warning">
                      Seeded / legacy incident — correlation metrics are not
                      available. This is not a Phase 7 correlated cluster.
                    </p>
                  ) : null}
                </div>
                <button
                  type="button"
                  disabled={isCorrelating}
                  onClick={() => void runCorrelate()}
                  className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-white/12 bg-white/4 px-3 text-xs font-semibold tracking-[0.08em]"
                >
                  {isCorrelating ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Radar className="size-3.5" />
                  )}
                  Run Correlation
                </button>
              </div>

              {selected.isCorrelated ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <MetaCard
                      label="STATUS"
                      value={STATUS_LABELS[selected.status]}
                    />
                    <MetaCard
                      label="SEVERITY"
                      value={SEVERITY_LABELS[selected.severity]}
                    />
                    <MetaCard
                      label="TREND"
                      value={`${trendArrow(selected.trend)} ${trendLabel(selected.trend)}`}
                    />
                    <MetaCard
                      label="CORRELATION"
                      value={`${formatScore(selected.correlationScore ?? detail?.incident.correlation_score)} / 100`}
                    />
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <MetaCard
                      label="REPORTS"
                      value={String(
                        detail?.incident.linked_report_count ??
                          detail?.incident.report_count ??
                          selected.evidence.reportCount,
                      )}
                    />
                    <MetaCard
                      label="INDEPENDENT"
                      value={String(
                        detail?.incident.independent_report_count ??
                          selected.independentReportCount,
                      )}
                    />
                    <MetaCard
                      label="AFFECTED RADIUS"
                      value={
                        (detail?.incident.radius_km ?? selected.radiusKm) !=
                        null
                          ? `${detail?.incident.radius_km ?? selected.radiusKm} km`
                          : "—"
                      }
                    />
                  </div>
                </>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <MetaCard label="ORIGIN" value={selected.origin.toUpperCase()} />
                  <MetaCard
                    label="LINKED REPORTS"
                    value={String(
                      detail?.incident.linked_report_count ??
                        selected.linkedReportCount,
                    )}
                  />
                  <MetaCard label="CORRELATION" value="—" />
                </div>
              )}

              {isDetailLoading ? (
                <p className="text-sm text-muted-foreground">Loading detail…</p>
              ) : null}

              {selected.isCorrelated && detail?.correlation_explanation ? (
                <CorrelationPanel factors={detail.correlation_explanation} />
              ) : null}

              {detail?.timeline?.length ? (
                <TimelinePanel events={detail.timeline} />
              ) : null}

              {detail?.reports?.length ? (
                <RelatedReportsPanel reports={detail.reports} />
              ) : (
                !isDetailLoading && (
                  <p className="text-sm text-muted-foreground">
                    No reports currently linked via incident_id.
                  </p>
                )
              )}

              <p className="flex items-start gap-2 text-xs text-muted-foreground">
                <ShieldAlert className="mt-0.5 size-3.5 text-warning" />
                Correlation assists clustering. It does not verify reports or
                guarantee a real-world event.
              </p>

              <Link
                href="/live-map"
                className="inline-flex items-center gap-1 text-sm text-weather-secondary"
              >
                Open live map <ArrowUpRight className="size-3.5" />
              </Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function MetaCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/3 px-3 py-2 ring-1 ring-white/8">
      <p className="text-[10px] tracking-[0.12em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}

function CorrelationPanel({ factors }: { factors: ApiCorrelationFactor[] }) {
  return (
    <div>
      <h3 className="text-section-title">Why these signals were correlated</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {factors.map((factor) => (
          <article
            key={factor.name}
            className="rounded-lg bg-white/3 px-3 py-3 ring-1 ring-white/8"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-[11px] font-semibold tracking-[0.1em] text-weather-secondary">
                {factorLabel(factor.name)}
              </p>
              <span className="font-mono text-xs">
                {formatScore(factor.score)} / 100
              </span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/8">
              <div
                className="h-full rounded-full bg-weather"
                style={{
                  width: `${Math.max(0, Math.min(100, factor.score))}%`,
                }}
              />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{factor.detail}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

function TimelinePanel({
  events,
}: {
  events: ApiIncidentDetail["timeline"];
}) {
  return (
    <div>
      <h3 className="text-section-title">Timeline</h3>
      <ol className="mt-3 space-y-2">
        {events.map((event) => (
          <li
            key={event.id}
            className="rounded-lg bg-white/3 px-3 py-2 ring-1 ring-white/8"
          >
            <div className="flex items-center gap-2">
              <Activity className="size-3.5 text-weather-secondary" />
              <p className="text-sm font-medium">{event.title}</p>
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              {new Date(event.occurred_at).toLocaleString("en-IN", {
                hour12: false,
                timeZone: "Asia/Kolkata",
              })}{" "}
              IST
              {event.detail ? ` · ${event.detail}` : ""}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}

function RelatedReportsPanel({ reports }: { reports: ApiReport[] }) {
  return (
    <div>
      <h3 className="text-section-title">Related reports</h3>
      <ul className="mt-3 space-y-2">
        {reports.map((report) => {
          const rejected = report.verification_status === "REJECTED";
          return (
            <li
              key={report.id}
              className={cn(
                "rounded-lg px-3 py-2 ring-1",
                rejected
                  ? "bg-critical/8 ring-critical/20 opacity-80"
                  : "bg-white/3 ring-white/8",
              )}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium">{report.title}</p>
                <span className="font-mono text-[11px] text-weather-secondary">
                  Evidence {formatScore(report.evidence_score)}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {report.status} · {report.source_type} ·{" "}
                {report.verification_status}
                {rejected ? " · does not strengthen cluster" : ""}
              </p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

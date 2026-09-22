"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { ArrowUpRight, Loader2 } from "lucide-react";

import { IncidentMap } from "@/components/command-center/incident-map";
import { StatusBadge } from "@/components/shared/status-badge";
import { useIncidents } from "@/hooks/use-incidents";
import { correlatedIncidents } from "@/lib/incidents/metrics";
import {
  SEVERITY_LABELS,
  trendArrow,
  trendLabel,
} from "@/lib/incidents/utils";
import { toNullableScore } from "@/lib/verification/format";
import type { OperationalStatus } from "@/types/status";

export function LiveMapWorkspace() {
  const { incidents, isLoading, error, source } = useIncidents();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const mapIncidents = useMemo(
    () => correlatedIncidents(incidents),
    [incidents],
  );

  const selected = useMemo(
    () => mapIncidents.find((i) => i.id === selectedId) ?? null,
    [mapIncidents, selectedId],
  );

  const correlationLabel = (() => {
    const n = toNullableScore(selected?.correlationScore);
    if (n === null) return null;
    return Number.isInteger(n) ? String(n) : n.toFixed(1);
  })();

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4">
      <header className="rounded-xl bg-surface/80 px-4 py-4 ring-1 ring-white/6 sm:px-5">
        <p className="text-label text-weather-secondary">Live operating picture</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Live Map</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Correlated weather incidents only — citizen reports are signals, not
          incidents. Source: {source === "api" ? "database" : "demo fallback"}.
        </p>
      </header>

      {error ? (
        <p className="rounded-lg border border-warning/25 bg-warning/10 px-3 py-2 text-sm">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-h-[32rem] overflow-hidden rounded-xl ring-1 ring-white/8">
          {isLoading && mapIncidents.length === 0 ? (
            <div className="flex h-full min-h-[32rem] items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading incidents…
            </div>
          ) : (
            <IncidentMap
              incidents={mapIncidents}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}
        </div>

        <aside className="rounded-xl bg-card/60 px-4 py-4 ring-1 ring-white/6">
          <h2 className="text-section-title">Selected incident</h2>
          {!selected ? (
            <p className="mt-3 text-sm text-muted-foreground">
              Select a marker to inspect incident intelligence.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              <p className="font-mono text-[11px] text-weather-secondary">
                {selected.code}
              </p>
              <p className="text-lg font-semibold">{selected.title}</p>
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={selected.status as OperationalStatus} />
                <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em]">
                  {SEVERITY_LABELS[selected.severity]}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                {trendArrow(selected.trend)} {trendLabel(selected.trend)} ·{" "}
                {selected.evidence.reportCount} reports
                {selected.independentReportCount
                  ? ` · ${selected.independentReportCount} independent`
                  : ""}
              </p>
              {correlationLabel ? (
                <p className="text-sm text-muted-foreground">
                  Correlation {correlationLabel} / 100
                </p>
              ) : null}
              <Link
                href="/incidents"
                className="inline-flex items-center gap-1 text-sm text-weather-secondary"
              >
                View Incident <ArrowUpRight className="size-3.5" />
              </Link>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

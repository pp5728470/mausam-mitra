"use client";

import { useCallback, useMemo, useState } from "react";

import { ActivityFeed } from "@/components/command-center/activity-feed";
import { CommandStatusStrip } from "@/components/command-center/command-status-strip";
import { EmergingSignals } from "@/components/command-center/emerging-signals";
import { IncidentMap } from "@/components/command-center/incident-map";
import { KpiStrip } from "@/components/command-center/kpi-strip";
import { SituationSummary } from "@/components/command-center/situation-summary";
import { TopIncidents } from "@/components/command-center/top-incidents";
import { TrendChart } from "@/components/command-center/trend-chart";
import { Skeleton } from "@/components/ui/skeleton";
import { useIncidents } from "@/hooks/use-incidents";
import {
  correlatedIncidents,
  deriveCommandKpis,
  deriveEmergingSignals,
  deriveSituationSummary,
  rankTopIncidents,
} from "@/lib/incidents/metrics";

function CommandCenterLoading() {
  return (
    <div
      className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 sm:gap-5"
      aria-busy="true"
      aria-label="Loading incident intelligence"
    >
      <Skeleton className="h-20 rounded-xl bg-white/5" />
      <Skeleton className="h-36 rounded-xl bg-white/5" />
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Skeleton className="h-24 rounded-xl bg-white/5" />
        <Skeleton className="h-24 rounded-xl bg-white/5" />
        <Skeleton className="h-24 rounded-xl bg-white/5" />
        <Skeleton className="h-24 rounded-xl bg-white/5" />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <Skeleton className="min-h-[28rem] rounded-xl bg-white/5" />
        <Skeleton className="min-h-[22rem] rounded-xl bg-white/5" />
      </div>
      <p className="text-center text-sm text-muted-foreground">
        Loading incident intelligence…
      </p>
    </div>
  );
}

export function CommandCenter() {
  const {
    incidents,
    isLoading,
    isRefreshing,
    error,
    source,
    hasResolved,
    refresh,
  } = useIncidents();

  const [userSelectedId, setUserSelectedId] = useState<string | null>(null);

  const mapIncidents = useMemo(
    () => correlatedIncidents(incidents),
    [incidents],
  );
  const topIncidents = useMemo(
    () => rankTopIncidents(incidents, 5),
    [incidents],
  );
  const summary = useMemo(
    () => deriveSituationSummary(incidents),
    [incidents],
  );
  const kpis = useMemo(() => deriveCommandKpis(incidents), [incidents]);
  const emerging = useMemo(
    () => deriveEmergingSignals(incidents, 3),
    [incidents],
  );

  const selectedId = useMemo(() => {
    const pool = mapIncidents.length > 0 ? mapIncidents : incidents;
    if (
      userSelectedId &&
      pool.some((incident) => incident.id === userSelectedId)
    ) {
      return userSelectedId;
    }
    return topIncidents[0]?.id ?? pool[0]?.id ?? null;
  }, [userSelectedId, incidents, mapIncidents, topIncidents]);

  const lastUpdatedLabel = useMemo(() => {
    if (incidents.length === 0) return "—";
    const latest = incidents.reduce((max, incident) => {
      const t = Date.parse(incident.lastSignalAt);
      return Number.isNaN(t) ? max : Math.max(max, t);
    }, 0);
    if (!latest) return "—";
    return (
      new Date(latest).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
        timeZone: "Asia/Kolkata",
      }) + " IST"
    );
  }, [incidents]);

  const handleSelect = useCallback((id: string | null) => {
    setUserSelectedId(id);
  }, []);

  const handleSelectRequired = useCallback((id: string) => {
    setUserSelectedId(id);
  }, []);

  if (isLoading && !hasResolved) {
    return <CommandCenterLoading />;
  }

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 sm:gap-5">
      <CommandStatusStrip
        source={source}
        backendUnavailable={source === "mock" && Boolean(error)}
        isRefreshing={isRefreshing}
        lastUpdatedLabel={lastUpdatedLabel}
        incidentCount={mapIncidents.length}
        onRefresh={refresh}
      />
      <SituationSummary summary={summary} />
      <KpiStrip kpis={kpis} />

      <section
        aria-label="Live incident map and top incidents"
        className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-stretch"
      >
        <IncidentMap
          incidents={mapIncidents}
          selectedId={selectedId}
          onSelect={handleSelect}
        />
        <div className="flex min-h-[22rem] flex-col gap-4 xl:min-h-0">
          <TopIncidents
            incidents={topIncidents}
            selectedId={selectedId}
            onSelect={handleSelectRequired}
          />
        </div>
      </section>

      <section
        aria-label="Emerging signals and live activity"
        className="grid gap-4 lg:grid-cols-2"
      >
        <EmergingSignals
          signals={emerging}
          selectedId={selectedId}
          onSelect={handleSelectRequired}
        />
        <ActivityFeed
          onSelectIncident={
            source === "mock" ? handleSelectRequired : undefined
          }
        />
      </section>

      <TrendChart />
    </div>
  );
}

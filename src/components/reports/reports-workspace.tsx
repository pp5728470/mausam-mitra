"use client";

import { useCallback, useState } from "react";
import { ClipboardPlus } from "lucide-react";

import { RecentReports } from "@/components/reports/recent-reports";
import { ReportIncidentForm } from "@/components/reports/report-incident-form";
import { useReports } from "@/hooks/use-reports";

import { useAuth } from "@/contexts/AuthContext";

export function ReportsWorkspace() {
  const { reports, total, isLoading, error, refresh } = useReports({
    limit: 40,
  });
  const { user } = useAuth();
  const [showForm, setShowForm] = useState(true);

  const handleSubmitted = useCallback(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-5">
      <header className="rounded-xl bg-surface/80 px-4 py-5 ring-1 ring-white/6 sm:px-6">
        <p className="text-label text-weather-secondary">Citizen signal intake</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Report Weather Incident
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground sm:text-base">
          Help build a clearer picture of what&apos;s happening on the ground.
        </p>
        <p className="mt-3 text-xs text-muted-foreground">
          Anonymous raw signal · Reviewed before any incident correlation · Not
          live weather verification
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-weather px-4 text-sm font-semibold text-slate-950 transition hover:bg-weather/90"
        >
          <ClipboardPlus className="size-4" aria-hidden />
          Report Incident
        </button>
        <button
          type="button"
          onClick={() => {
            setShowForm(false);
            refresh();
          }}
          className="inline-flex min-h-11 items-center rounded-lg border border-white/12 bg-white/4 px-4 text-sm font-medium text-foreground transition hover:bg-white/8"
        >
          Recent reports
        </button>
      </div>

      {showForm ? (
        <section
          aria-label="Citizen report form"
          className="rounded-xl bg-card/60 px-4 py-5 ring-1 ring-white/6 sm:px-6"
        >
          <ReportIncidentForm onSubmitted={handleSubmitted} />
        </section>
      ) : null}

      <RecentReports
        reports={reports}
        total={total}
        isLoading={isLoading}
        error={error}
        onRefresh={refresh}
        showVerificationStatus={user?.role === "CITIZEN"}
      />
    </div>
  );
}

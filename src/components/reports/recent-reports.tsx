"use client";

import { RefreshCw } from "lucide-react";

import type { ReportListItem } from "@/lib/api/adapters/reports";
import { cn } from "@/lib/utils";
import type { ApiReportStatus } from "@/lib/api/types";

const STATUS_TONE: Record<ApiReportStatus, string> = {
  NEW: "bg-weather/15 text-weather-secondary ring-weather/25",
  PROCESSING: "bg-warning/15 text-warning ring-warning/25",
  CORRELATED: "bg-success/15 text-success ring-success/25",
  REJECTED: "bg-critical/15 text-critical ring-critical/25",
};

type RecentReportsProps = {
  reports: ReportListItem[];
  total: number;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  showVerificationStatus?: boolean;
};

export function RecentReports({
  reports,
  total,
  isLoading,
  error,
  onRefresh,
  showVerificationStatus = false,
}: RecentReportsProps) {
  return (
    <section
      aria-labelledby="recent-reports-heading"
      className="rounded-xl bg-card/60 px-4 py-4 ring-1 ring-white/6 sm:px-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-label text-weather-secondary">Ingestion queue</p>
          <h2
            id="recent-reports-heading"
            className="text-section-title mt-0.5"
          >
            Recent Reports
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Raw signals from citizens and other sources — not verified
            incidents.
          </p>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/4 px-2.5 py-1 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground transition hover:bg-white/8 hover:text-foreground"
        >
          <RefreshCw
            className={cn("size-3", isLoading && "animate-spin")}
            aria-hidden
          />
          REFRESH
        </button>
      </div>

      {error ? (
        <p className="mt-4 rounded-lg border border-critical/25 bg-critical/10 px-3 py-2 text-sm text-foreground">
          Unable to load reports. {error}
        </p>
      ) : null}

      {isLoading && reports.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">Loading reports…</p>
      ) : null}

      {!isLoading && !error && reports.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">
          No reports yet. Submit the first citizen signal above.
        </p>
      ) : null}

      {reports.length > 0 ? (
        <ul className="mt-4 divide-y divide-white/6">
          {reports.map((report) => (
            <li key={report.id} className="py-3 first:pt-0 last:pb-0">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">
                    {report.title}
                  </p>
                  <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                    {report.publicId} · {report.locationLabel}
                </p>
              </div>
              <span
                className={cn(
                  "rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-[0.08em] ring-1",
                  showVerificationStatus 
                    ? (report.verificationStatus === "VERIFIED" ? "bg-success/15 text-success ring-success/25" : 
                       report.verificationStatus === "REJECTED" ? "bg-critical/15 text-critical ring-critical/25" : 
                       "bg-warning/15 text-warning ring-warning/25")
                    : STATUS_TONE[report.status]
                )}
              >
                {showVerificationStatus ? report.verificationStatus.replace("_", " ") : report.status}
              </span>
            </div>
            <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
              <span>
                Source:{" "}
                <span className="text-foreground/85">{report.sourceType}</span>
              </span>
              <span>{report.receivedLabel}</span>
              {report.classification ? (
                <span>
                  Category:{" "}
                  <span className="text-foreground/85">
                    {report.classification}
                  </span>
                </span>
              ) : null}
              {showVerificationStatus ? null : (
                <span>
                  Incident:{" "}
                  <span className="text-foreground/85">
                    {report.incidentId ? "Linked" : "None"}
                  </span>
                </span>
              )}
            </div>
          </li>
          ))}
        </ul>
      ) : null}

      {total > reports.length ? (
        <p className="mt-3 text-[11px] text-muted-foreground">
          Showing {reports.length} of {total} reports
        </p>
      ) : null}
    </section>
  );
}

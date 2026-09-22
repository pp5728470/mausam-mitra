"use client";

import { RefreshCw } from "lucide-react";

import type { IncidentDataSource } from "@/hooks/use-incidents";
import { cn } from "@/lib/utils";

export type DataSourceKind = IncidentDataSource;

type DataSourceIndicatorProps = {
  source: DataSourceKind;
  /** Present when mock fallback was used after a failed API call. */
  backendUnavailable?: boolean;
  isRefreshing?: boolean;
  onRefresh?: () => void;
  className?: string;
};

function labelFor(
  source: DataSourceKind,
  backendUnavailable: boolean,
): string {
  if (source === "api") return "LIVE BACKEND";
  if (backendUnavailable) return "BACKEND UNAVAILABLE · DEMO DATA";
  return "SIMULATED OPERATING PICTURE";
}

/**
 * Subtle Command Center badge distinguishing database-backed vs mock data.
 * Does not claim live weather — only whether FastAPI/PostGIS responded.
 */
export function DataSourceIndicator({
  source,
  backendUnavailable = false,
  isRefreshing = false,
  onRefresh,
  className,
}: DataSourceIndicatorProps) {
  const label = labelFor(source, backendUnavailable);
  const live = source === "api";

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 text-[10px] font-semibold tracking-[0.12em]",
        className,
      )}
    >
      <span
        className={cn(
          "rounded-full border px-2 py-0.5",
          live
            ? "border-success/30 bg-success/10 text-success"
            : "border-warning/25 bg-warning/8 text-warning",
        )}
        title={
          live
            ? "Incidents loaded from FastAPI / PostGIS (simulated seed records)"
            : "Showing frontend mock demo incidents"
        }
      >
        {label}
      </span>
      {onRefresh ? (
        <button
          type="button"
          onClick={onRefresh}
          disabled={isRefreshing}
          className={cn(
            "inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/4 px-2 py-0.5 text-muted-foreground transition-colors hover:bg-white/8 hover:text-foreground",
            isRefreshing && "opacity-60",
          )}
          aria-label="Refresh incidents from backend"
        >
          <RefreshCw
            className={cn("size-3", isRefreshing && "animate-spin")}
            aria-hidden
          />
          <span className="tracking-[0.1em]">REFRESH</span>
        </button>
      ) : null}
    </div>
  );
}

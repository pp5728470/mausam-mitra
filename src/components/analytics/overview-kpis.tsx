import type { AnalyticsOverview } from "@/lib/api/analytics";

interface OverviewKPIsProps {
  overview: AnalyticsOverview;
}

export function OverviewKPIs({ overview }: OverviewKPIsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
      {/* KPI 1: Reports */}
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Total Reports
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">
            {overview.total_reports}
          </span>
          <span className="text-xs text-muted-foreground">
            (+{overview.reports_last_7d} this week)
          </span>
        </div>
      </div>

      {/* KPI 2: Incidents */}
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Total Incidents
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">
            {overview.total_incidents}
          </span>
          <span className="text-xs text-muted-foreground">
            {overview.correlated_incidents} correlated
          </span>
        </div>
      </div>

      {/* KPI 3: Active Incidents */}
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Active Incidents
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">
            {overview.active_incidents}
          </span>
          <span className="text-xs text-rose-400">
            {overview.critical_incidents} critical
          </span>
        </div>
      </div>

      {/* KPI 4: Verified Reports */}
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Verified Reports
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">
            {overview.verified_reports}
          </span>
          <span className="text-xs text-muted-foreground">
            {overview.under_review_reports} under review
          </span>
        </div>
      </div>

      {/* KPI 5: Correlation Rate */}
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Correlation Rate
        </p>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">
            {overview.correlation_rate.toFixed(1)}%
          </span>
          <span className="text-xs text-muted-foreground">
            reports linked
          </span>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useAnalytics } from "@/hooks/use-analytics";
import { OverviewKPIs } from "./overview-kpis";
import { TrendsChart } from "./trends-chart";
import { CategoryChart } from "./category-chart";
import { SeverityChart } from "./severity-chart";
import { WeatherMetrics } from "./weather-metrics";
import { ClassificationIntelligence } from "./classification-intelligence";
import { MapPin, RefreshCcw } from "lucide-react";

type TimeRange = 1 | 7 | 30;

function getClusterLocationLabel(lat: number, lng: number): string {
  const centers = [
    { name: "Wakad / Hinjewadi, Pune", lat: 18.598, lng: 73.756 },
    { name: "Shivajinagar, Pune", lat: 18.520, lng: 73.856 },
    { name: "Bandra / Kurla, Mumbai", lat: 19.076, lng: 72.877 },
    { name: "Panchavati, Nashik", lat: 20.006, lng: 73.790 },
    { name: "Civil Lines, Nagpur", lat: 21.146, lng: 79.088 },
  ];
  for (const c of centers) {
    if (Math.abs(lat - c.lat) < 0.2 && Math.abs(lng - c.lng) < 0.2) {
      return c.name;
    }
  }
  return `${lat.toFixed(2)}°N, ${lng.toFixed(2)}°E`;
}

export function AnalyticsWorkspace() {
  const [timeRange, setTimeRange] = useState<TimeRange>(7);
  const { overview, trends, categories, severity, geography, weather, isLoading, refresh } = useAnalytics(timeRange);

  if (isLoading && !overview) {
    return (
      <div className="flex min-h-[500px] w-full items-center justify-center">
        <RefreshCcw className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!overview || !trends || !categories || !severity || !geography || !weather) {
    return (
      <div className="flex min-h-[500px] w-full flex-col items-center justify-center gap-2">
        <p className="text-muted-foreground">Failed to load analytics</p>
        <button onClick={refresh} className="text-sm text-blue-500 hover:underline">
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-6">
      {/* HEADER & FILTER */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Analytics & Intelligence
          </h1>
          <p className="text-sm text-muted-foreground">
            Operational dashboard built from live backend aggregation.
          </p>
        </div>
        
        <div className="flex items-center gap-1 rounded-lg bg-white/5 p-1 ring-1 ring-white/10">
          {[1, 7, 30].map((val) => (
            <button
              key={val}
              onClick={() => setTimeRange(val as TimeRange)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
                timeRange === val
                  ? "bg-white/10 text-white shadow"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              }`}
            >
              {val === 1 ? "24h" : `${val}d`}
            </button>
          ))}
        </div>
      </div>

      {/* KPI STRIP */}
      <OverviewKPIs overview={overview} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* TIME SERIES */}
        <div className="col-span-1 lg:col-span-2 rounded-xl border border-white/10 bg-card/40 p-6">
          <h2 className="text-base font-semibold text-foreground mb-6">Report Volume Trend</h2>
          <TrendsChart trends={trends} timeRange={timeRange} />
        </div>

        {/* WEATHER METRICS */}
        <div className="rounded-xl border border-white/10 bg-card/40 p-6 flex flex-col">
          <h2 className="text-base font-semibold text-foreground mb-6">Weather Context</h2>
          <WeatherMetrics weather={weather} />
        </div>

        {/* CATEGORY DIST */}
        <div className="rounded-xl border border-white/10 bg-card/40 p-6">
          <h2 className="text-base font-semibold text-foreground mb-6">Incident Categories</h2>
          {categories.distribution.length > 0 ? (
            <CategoryChart categories={categories} />
          ) : (
            <p className="text-sm text-muted-foreground text-center mt-10">No category data</p>
          )}
        </div>

        {/* SEVERITY DIST */}
        <div className="rounded-xl border border-white/10 bg-card/40 p-6">
          <h2 className="text-base font-semibold text-foreground mb-6">Severity Distribution</h2>
          {severity.distribution.length > 0 ? (
            <SeverityChart severity={severity} />
          ) : (
            <p className="text-sm text-muted-foreground text-center mt-10">No severity data</p>
          )}
        </div>

        {/* CLASSIFICATION */}
        <div className="rounded-xl border border-white/10 bg-card/40 p-6">
          <h2 className="text-base font-semibold text-foreground mb-6">Classification Intelligence</h2>
          <ClassificationIntelligence overview={overview} />
        </div>

        {/* GEOGRAPHY / VERIFICATION */}
        <div className="rounded-xl border border-white/10 bg-card/40 p-6 lg:col-span-3">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-base font-semibold text-foreground">Geographic Concentration</h2>
            <span className="text-xs text-muted-foreground">Top Spatial Clusters</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {geography.points.length > 0 ? (
              geography.points.slice(0, 4).map((pt, i) => (
                <div key={i} className="flex items-start gap-3 p-3.5 rounded-lg bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-weather/10 text-weather mt-0.5">
                    <MapPin className="size-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground truncate" title={getClusterLocationLabel(pt.latitude, pt.longitude)}>
                      {getClusterLocationLabel(pt.latitude, pt.longitude)}
                    </p>
                    <p className="text-xs text-muted-foreground font-mono mt-0.5">
                      {pt.latitude.toFixed(3)}°, {pt.longitude.toFixed(3)}°
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="inline-flex items-center rounded-md bg-white/6 px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                        {pt.report_count} {pt.report_count === 1 ? "report" : "reports"}
                      </span>
                      {pt.incident_count > 0 && (
                        <span className="inline-flex items-center rounded-md bg-weather-secondary/15 px-1.5 py-0.5 text-[11px] font-medium text-weather-secondary">
                          {pt.incident_count} {pt.incident_count === 1 ? "incident" : "incidents"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No geographic clusters identified in this period.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

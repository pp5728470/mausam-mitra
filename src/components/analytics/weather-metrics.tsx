import type { AnalyticsWeather } from "@/lib/api/analytics";
import { CloudSun } from "lucide-react";

interface WeatherMetricsProps {
  weather: AnalyticsWeather;
}

export function WeatherMetrics({ weather }: WeatherMetricsProps) {
  if (weather.observation_count === 0) {
    return (
      <div className="flex h-[200px] w-full flex-col items-center justify-center rounded-xl border border-dashed border-white/12 bg-white/3 p-6 text-center">
        <div className="flex size-10 items-center justify-center rounded-full bg-weather/10 text-weather mb-3">
          <CloudSun className="size-5" />
        </div>
        <p className="text-sm font-medium text-foreground">Weather Ingestion Ready</p>
        <p className="mt-1 max-w-xs text-xs text-muted-foreground leading-relaxed">
          OpenWeatherMap provider configured. Ground telemetry gathers automatically when active incidents correlate.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Avg Temp</p>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="text-2xl font-semibold text-foreground">
            {weather.average_temperature?.toFixed(1) ?? "--"}
          </span>
          <span className="text-sm text-muted-foreground">°C</span>
        </div>
      </div>
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Max Temp</p>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="text-2xl font-semibold text-foreground">
            {weather.maximum_temperature?.toFixed(1) ?? "--"}
          </span>
          <span className="text-sm text-muted-foreground">°C</span>
        </div>
      </div>
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Avg Humidity</p>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="text-2xl font-semibold text-foreground">
            {weather.average_humidity?.toFixed(0) ?? "--"}
          </span>
          <span className="text-sm text-muted-foreground">%</span>
        </div>
      </div>
      <div className="rounded-xl border border-white/10 bg-card/40 p-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Avg Wind</p>
        <div className="mt-1 flex items-baseline gap-1">
          <span className="text-2xl font-semibold text-foreground">
            {weather.average_wind_speed?.toFixed(1) ?? "--"}
          </span>
          <span className="text-sm text-muted-foreground">m/s</span>
        </div>
      </div>
      <div className="col-span-2 text-xs text-muted-foreground text-right mt-2">
        Based on {weather.observation_count} observations in the selected period.
      </div>
    </div>
  );
}

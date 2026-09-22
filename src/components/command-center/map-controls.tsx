"use client";

import { cn } from "@/lib/utils";
import type { IncidentSeverity } from "@/types/incident";

export type MapLayerKey =
  | "incidents"
  | "weather"
  | "reports"
  | "verified"
  | "emerging";

export type MapControlsState = {
  layers: Record<MapLayerKey, boolean>;
  severity: IncidentSeverity | "all";
};

type MapControlsProps = {
  value: MapControlsState;
  onChange: (next: MapControlsState) => void;
};

const LAYER_OPTIONS: {
  key: MapLayerKey;
  label: string;
  functional: boolean;
}[] = [
  { key: "incidents", label: "Incidents", functional: true },
  { key: "weather", label: "Weather", functional: false },
  { key: "reports", label: "Reports", functional: false },
  { key: "verified", label: "Verified", functional: true },
  { key: "emerging", label: "Emerging", functional: true },
];

const SEVERITY_OPTIONS: { value: IncidentSeverity | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
];

export function MapControls({ value, onChange }: MapControlsProps) {
  return (
    <div
      className="pointer-events-auto w-[min(100%,16.5rem)] rounded-xl bg-popover/95 p-3 shadow-lg ring-1 ring-white/10 backdrop-blur-sm"
      role="group"
      aria-label="Map layer and severity controls"
    >
      <p className="text-label mb-2">Layers</p>
      <div className="flex flex-wrap gap-1.5">
        {LAYER_OPTIONS.map((layer) => {
          const active = value.layers[layer.key];
          return (
            <button
              key={layer.key}
              type="button"
              aria-pressed={active}
              title={
                layer.functional
                  ? undefined
                  : "Demo control — layer wiring comes in a later phase"
              }
              onClick={() => {
                if (!layer.functional) return;
                onChange({
                  ...value,
                  layers: {
                    ...value.layers,
                    [layer.key]: !active,
                  },
                });
              }}
              className={cn(
                "rounded-md px-2 py-1 text-[11px] font-medium tracking-wide transition-colors",
                !layer.functional && "cursor-default opacity-55",
                active && layer.functional
                  ? "bg-weather/15 text-weather-secondary ring-1 ring-weather/25"
                  : "bg-white/4 text-muted-foreground",
                layer.functional &&
                  !active &&
                  "hover:bg-white/7 hover:text-foreground",
              )}
            >
              {layer.label}
              {!layer.functional ? (
                <span className="ml-1 text-[9px] tracking-normal opacity-70">
                  soon
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <p className="text-label mt-3 mb-2">Severity</p>
      <div
        className="flex flex-wrap gap-1.5"
        role="radiogroup"
        aria-label="Severity filter"
      >
        {SEVERITY_OPTIONS.map((option) => {
          const active = value.severity === option.value;
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => onChange({ ...value, severity: option.value })}
              className={cn(
                "rounded-md px-2 py-1 text-[11px] font-medium tracking-wide transition-colors",
                active
                  ? "bg-white/10 text-foreground ring-1 ring-white/15"
                  : "bg-white/4 text-muted-foreground hover:bg-white/7 hover:text-foreground",
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

"use client";

import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";

import { StatusBadge } from "@/components/shared/status-badge";
import {
  SEVERITY_COLORS,
  SEVERITY_LABELS,
  trendArrow,
  trendLabel,
} from "@/lib/incidents/utils";
import { fadeUp, subtleTransition } from "@/lib/motion";
import { cn } from "@/lib/utils";
import type { Incident } from "@/types/incident";
import type { OperationalStatus } from "@/types/status";

type TopIncidentsProps = {
  incidents: Incident[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function TopIncidents({
  incidents,
  selectedId,
  onSelect,
}: TopIncidentsProps) {
  const reduceMotion = useSafeReducedMotion();

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={fadeUp}
      transition={subtleTransition}
      aria-labelledby="top-incidents-heading"
      className="flex h-full flex-col rounded-xl bg-card/60 ring-1 ring-white/6"
    >
      <div className="border-b border-white/6 px-4 py-3">
        <p className="text-label">Intelligence Queue</p>
        <h2 id="top-incidents-heading" className="text-section-title mt-0.5">
          Top Incidents
        </h2>
      </div>

      <ul className="flex-1 divide-y divide-white/5 overflow-y-auto">
        {incidents.map((incident) => {
          const selected = incident.id === selectedId;
          return (
            <li key={incident.id}>
              <button
                type="button"
                onClick={() => onSelect(incident.id)}
                aria-pressed={selected}
                className={cn(
                  "flex w-full items-start gap-3 px-4 py-3 text-left transition-colors",
                  selected
                    ? "bg-weather/10"
                    : "hover:bg-white/4 focus-visible:bg-white/4",
                )}
              >
                <span
                  className="mt-1.5 size-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: SEVERITY_COLORS[incident.severity] }}
                  aria-hidden
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-foreground">
                    {incident.title}
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-muted-foreground">
                    {incident.locationLabel}
                  </span>
                  <span className="mt-2 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] font-semibold tracking-[0.1em] text-muted-foreground">
                      {SEVERITY_LABELS[incident.severity]}
                    </span>
                    <StatusBadge status={incident.status as OperationalStatus} />
                  </span>
                  <span className="mt-2 flex items-center justify-between gap-2 text-[11px]">
                    <span className="text-success">
                      {incident.evidence.strength}% evidence
                    </span>
                    <span className="text-muted-foreground">
                      {trendArrow(incident.trend)} {trendLabel(incident.trend)}
                    </span>
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </motion.section>
  );
}

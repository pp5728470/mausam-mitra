"use client";

import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";

import { DataSourceIndicator } from "@/components/command-center/data-source-indicator";
import { VerificationPulse } from "@/components/command-center/verification-pulse";
import { LiveDot } from "@/components/shared/live-dot";
import type { IncidentDataSource } from "@/hooks/use-incidents";
import { fadeUp, subtleTransition } from "@/lib/motion";

type CommandStatusStripProps = {
  source: IncidentDataSource;
  backendUnavailable: boolean;
  isRefreshing: boolean;
  lastUpdatedLabel: string;
  incidentCount: number;
  onRefresh: () => void;
};

export function CommandStatusStrip({
  source,
  backendUnavailable,
  isRefreshing,
  lastUpdatedLabel,
  incidentCount,
  onRefresh,
}: CommandStatusStripProps) {
  const reduceMotion = useSafeReducedMotion();
  const live = source === "api";

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={fadeUp}
      transition={subtleTransition}
      aria-label="Command status"
      className="flex flex-col gap-3 rounded-xl bg-card/55 px-4 py-3 ring-1 ring-white/6"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-label text-weather-secondary">
            National Weather Intelligence
          </p>
          <DataSourceIndicator
            source={source}
            backendUnavailable={backendUnavailable}
            isRefreshing={isRefreshing}
            onRefresh={onRefresh}
          />
        </div>
        <h2 className="mt-1 text-sm font-medium text-foreground">
          Operating Picture
        </h2>
        <p className="mt-1 text-[11px] text-muted-foreground">
          {live
            ? "Database incidents via FastAPI · simulated weather seed (not live IMD)"
            : "Frontend demo incidents · connect FastAPI for database operating picture"}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
        <LiveDot
          label={live ? "SYSTEM LIVE" : "DEMO MODE"}
          className={
            live
              ? "text-[11px] font-semibold tracking-[0.08em] text-success"
              : "text-[11px] font-semibold tracking-[0.08em] text-warning"
          }
        />
        <span>
          Incidents:{" "}
          <span className="font-mono text-foreground/90">{incidentCount}</span>
        </span>
        <span>
          Last updated:{" "}
          <span className="font-mono text-foreground/90">
            {lastUpdatedLabel}
          </span>
        </span>
      </div>
      </div>
      <div className="border-t border-white/6 pt-2">
        <VerificationPulse />
      </div>
    </motion.section>
  );
}

"use client";

import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";

import { fadeUp, subtleTransition } from "@/lib/motion";
import type { SituationSummary as SituationSummaryData } from "@/types/incident";

type SituationSummaryProps = {
  summary: SituationSummaryData;
};

export function SituationSummary({ summary }: SituationSummaryProps) {
  const reduceMotion = useSafeReducedMotion();

  const stats = [
    {
      label: "Active Weather Incidents",
      value: summary.activeIncidents,
      tone: "text-weather-secondary",
    },
    {
      label: "Emerging",
      value: summary.emerging,
      tone: "text-warning",
    },
    {
      label: "Under Verification",
      value: summary.underVerification,
      tone: "text-muted-foreground",
    },
    {
      label: "Critical",
      value: summary.critical,
      tone: "text-critical",
    },
  ] as const;

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={fadeUp}
      transition={{ ...subtleTransition, delay: 0.04 }}
      aria-labelledby="national-situation-heading"
      className="rounded-xl bg-surface/80 px-4 py-4 ring-1 ring-white/6 sm:px-5"
    >
      <p className="text-label">National Situation</p>
      <h2
        id="national-situation-heading"
        className="mt-1 text-lg font-semibold tracking-tight text-foreground sm:text-xl"
      >
        {summary.activeIncidents} Active Weather Incidents
      </h2>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="min-w-0">
            <p
              className={`text-metric text-[1.65rem] sm:text-[1.85rem] ${stat.tone}`}
            >
              {String(stat.value).padStart(2, "0")}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </div>

      <p className="mt-4 text-sm text-foreground/85">
        <span className="mr-1.5 text-warning" aria-hidden>
          ↑
        </span>
        Situation trend: {summary.trendLabel}
      </p>
    </motion.section>
  );
}

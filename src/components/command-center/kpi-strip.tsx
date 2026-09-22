"use client";

import {
  Activity,
  BadgeCheck,
  CloudLightning,
  FileText,
} from "lucide-react";
import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";

import { fadeUp, staggerContainer, subtleTransition } from "@/lib/motion";
import { cn } from "@/lib/utils";
import type { CommandKpi } from "@/types/incident";

const TONE_STYLES: Record<
  CommandKpi["tone"],
  { icon: string; value: string; ring: string }
> = {
  active: {
    icon: "bg-weather/12 text-weather-secondary",
    value: "text-weather-secondary",
    ring: "ring-weather/15",
  },
  emerging: {
    icon: "bg-warning/12 text-warning",
    value: "text-warning",
    ring: "ring-warning/15",
  },
  verified: {
    icon: "bg-success/12 text-success",
    value: "text-success",
    ring: "ring-success/15",
  },
  reports: {
    icon: "bg-rain/12 text-rain",
    value: "text-rain",
    ring: "ring-rain/15",
  },
};

const ICONS = {
  active: CloudLightning,
  emerging: Activity,
  verified: BadgeCheck,
  reports: FileText,
} as const;

type KpiStripProps = {
  kpis: CommandKpi[];
};

export function KpiStrip({ kpis }: KpiStripProps) {
  const reduceMotion = useSafeReducedMotion();

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={staggerContainer}
      aria-label="Key performance indicators"
      className="grid grid-cols-2 gap-3 xl:grid-cols-4"
    >
      {kpis.map((kpi) => {
        const Icon = ICONS[kpi.tone];
        const tone = TONE_STYLES[kpi.tone];

        return (
          <motion.article
            key={kpi.id}
            variants={fadeUp}
            transition={subtleTransition}
            className={cn(
              "rounded-xl bg-card/60 px-3.5 py-3 ring-1",
              tone.ring,
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-label">{kpi.label}</p>
              <span
                className={cn(
                  "flex size-7 items-center justify-center rounded-lg",
                  tone.icon,
                )}
                aria-hidden
              >
                <Icon className="size-3.5" />
              </span>
            </div>
            <p className={cn("text-metric mt-2 text-[1.75rem]", tone.value)}>
              {kpi.displayValue}
            </p>
            <p className="mt-1 text-xs font-medium text-foreground/80">
              {kpi.trend}
            </p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {kpi.support}
            </p>
          </motion.article>
        );
      })}
    </motion.section>
  );
}

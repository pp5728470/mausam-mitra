"use client";

import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";

import { fadeUp, subtleTransition } from "@/lib/motion";
import { cn } from "@/lib/utils";
import type { EmergingSignal } from "@/types/incident";

type EmergingSignalsProps = {
  signals: EmergingSignal[];
  selectedId: string | null;
  onSelect: (incidentId: string) => void;
};

export function EmergingSignals({
  signals,
  selectedId,
  onSelect,
}: EmergingSignalsProps) {
  const reduceMotion = useSafeReducedMotion();

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={fadeUp}
      transition={{ ...subtleTransition, delay: 0.08 }}
      aria-labelledby="emerging-signals-heading"
      className="rounded-xl bg-card/60 px-4 py-3.5 ring-1 ring-warning/15"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-label text-warning">Signal Density</p>
        <span className="rounded-full border border-warning/20 bg-warning/8 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em] text-warning">
          FROM INCIDENT DATA
        </span>
      </div>
      <h2 id="emerging-signals-heading" className="text-section-title mt-0.5">
        Emerging Signals
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Derived from incident status/trend attributes — not a detection
        algorithm yet.
      </p>

      {signals.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">
          No emerging clusters in the current incident set.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {signals.map((signal) => (
            <li key={signal.id}>
              <button
                type="button"
                onClick={() => onSelect(signal.incidentId)}
                className={cn(
                  "flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left transition-colors",
                  selectedId === signal.incidentId
                    ? "bg-warning/10 ring-1 ring-warning/20"
                    : "bg-white/3 hover:bg-white/5",
                )}
              >
                <span className="text-sm font-medium text-foreground">
                  {signal.city}
                </span>
                <span className="font-mono text-xs text-warning">
                  +{signal.reportsDelta} reports / {signal.windowLabel}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </motion.section>
  );
}

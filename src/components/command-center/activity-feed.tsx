"use client";

import { motion } from "motion/react";
import { useSafeReducedMotion } from "@/hooks/use-safe-reduced-motion";

import { mockActivity } from "@/lib/mock/activity";
import { fadeUp, subtleTransition } from "@/lib/motion";
import { cn } from "@/lib/utils";
import type { ActivityEventKind } from "@/types/incident";

const KIND_DOT: Record<ActivityEventKind, string> = {
  citizen_report: "bg-weather-secondary",
  evidence_update: "bg-rain",
  cluster_expanded: "bg-warning",
  verification_completed: "bg-success",
  signal_spike: "bg-critical",
};

type ActivityFeedProps = {
  onSelectIncident?: (incidentId: string) => void;
};

export function ActivityFeed({ onSelectIncident }: ActivityFeedProps) {
  const reduceMotion = useSafeReducedMotion();

  return (
    <motion.section
      initial={reduceMotion ? false : "hidden"}
      animate="visible"
      variants={fadeUp}
      transition={{ ...subtleTransition, delay: 0.1 }}
      aria-labelledby="activity-feed-heading"
      className="rounded-xl bg-card/60 px-4 py-3.5 ring-1 ring-white/6"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-label">Live Stream</p>
        <span className="rounded-full border border-white/10 bg-white/4 px-2 py-0.5 text-[10px] font-semibold tracking-[0.1em] text-muted-foreground">
          DEMO ACTIVITY
        </span>
      </div>
      <h2 id="activity-feed-heading" className="text-section-title mt-0.5">
        Live Activity
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Simulated activity timeline — not sourced from FastAPI.
      </p>

      <ol className="relative mt-4 space-y-0">
        <span
          className="absolute top-1 bottom-1 left-[0.28rem] w-px bg-white/8"
          aria-hidden
        />
        {mockActivity.map((event, index) => {
          const interactive = Boolean(event.incidentId && onSelectIncident);
          const content = (
            <>
              <span
                className={cn(
                  "relative z-10 mt-1 size-2.5 shrink-0 rounded-full ring-4 ring-background",
                  KIND_DOT[event.kind],
                )}
                aria-hidden
              />
              <span className="min-w-0 flex-1 pb-3">
                <span className="flex items-baseline gap-2">
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {event.time}
                  </span>
                  <span className="text-sm text-foreground">{event.title}</span>
                </span>
                <span className="mt-0.5 block text-xs text-muted-foreground">
                  {event.detail}
                </span>
              </span>
            </>
          );

          return (
            <li key={event.id}>
              {interactive && event.incidentId ? (
                <button
                  type="button"
                  onClick={() => onSelectIncident?.(event.incidentId!)}
                  className={cn(
                    "flex w-full gap-3 rounded-lg px-1 py-0.5 text-left transition-colors hover:bg-white/3",
                    index === 0 && "pt-0",
                  )}
                >
                  {content}
                </button>
              ) : (
                <div className="flex gap-3 px-1">{content}</div>
              )}
            </li>
          );
        })}
      </ol>
    </motion.section>
  );
}

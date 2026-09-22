"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  SEVERITY_LABELS,
  trendArrow,
  trendLabel,
} from "@/lib/incidents/utils";
import type { Incident } from "@/types/incident";
import type { OperationalStatus } from "@/types/status";

type IncidentPreviewProps = {
  incident: Incident | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function IncidentPreview({
  incident,
  open,
  onOpenChange,
}: IncidentPreviewProps) {
  if (!incident) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" showCloseButton>
        <DialogHeader>
          <p className="text-label text-weather-secondary">Incident Preview</p>
          <p className="font-mono text-[11px] text-weather-secondary">
            {incident.code}
          </p>
          <DialogTitle className="text-lg tracking-tight uppercase">
            {incident.title}
          </DialogTitle>
          <DialogDescription className="sr-only">
            Simulated incident details for {incident.title}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-semibold tracking-[0.12em] text-foreground">
            {SEVERITY_LABELS[incident.severity]}
          </span>
          <StatusBadge status={incident.status as OperationalStatus} />
        </div>

        <div className="grid grid-cols-2 gap-3 rounded-lg bg-white/3 p-3 ring-1 ring-white/6">
          <div>
            <p className="text-caption">Reports</p>
            <p className="mt-0.5 font-mono text-lg font-semibold text-foreground">
              {incident.evidence.reportCount}
            </p>
          </div>
          <div>
            <p className="text-caption">Evidence strength</p>
            <p className="mt-0.5 font-mono text-lg font-semibold text-success">
              {incident.evidence.strength}%
            </p>
          </div>
        </div>

        <p className="text-sm text-foreground/90">
          <span className="mr-1.5 text-warning" aria-hidden>
            {trendArrow(incident.trend)}
          </span>
          {trendLabel(incident.trend)}
        </p>

        <p className="text-xs text-muted-foreground">
          Last signal: {incident.lastSignalAgo}
        </p>

        <div>
          <p className="text-label mb-2">Sources</p>
          <ul className="space-y-1">
            {incident.evidence.sources.map((source) => (
              <li key={source} className="text-xs text-foreground/85">
                · {source}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-[11px] text-muted-foreground">
          Demo intelligence only — not a live government feed.
        </p>

        <Button asChild className="w-full">
          <Link href="/incidents">
            View Incident
            <ArrowUpRight data-icon="inline-end" />
          </Link>
        </Button>
      </DialogContent>
    </Dialog>
  );
}

type IncidentPreviewCardProps = {
  incident: Incident;
  onView: () => void;
  className?: string;
};

export function IncidentPreviewCard({
  incident,
  onView,
  className,
}: IncidentPreviewCardProps) {
  return (
    <aside
      className={className}
      aria-label={`Selected incident: ${incident.title}`}
    >
      <div className="rounded-xl bg-popover/95 p-3.5 shadow-lg ring-1 ring-white/10 backdrop-blur-sm">
        <p className="font-mono text-[10px] text-weather-secondary">
          {incident.code}
        </p>
        <p className="mt-0.5 text-[11px] font-semibold tracking-[0.14em] text-foreground uppercase">
          {incident.title}
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] font-semibold tracking-[0.1em] text-muted-foreground">
            {SEVERITY_LABELS[incident.severity]}
          </span>
          <span className="text-muted-foreground/40">·</span>
          <StatusBadge status={incident.status as OperationalStatus} />
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <p>
            <span className="font-mono text-foreground">
              {incident.evidence.reportCount}
            </span>{" "}
            <span className="text-muted-foreground">reports</span>
          </p>
          <p>
            <span className="font-mono text-success">
              {incident.evidence.strength}%
            </span>{" "}
            <span className="text-muted-foreground">evidence</span>
          </p>
        </div>
        <p className="mt-2 text-xs text-foreground/85">
          {trendArrow(incident.trend)} {trendLabel(incident.trend)}
        </p>
        <p className="mt-1 text-[11px] text-muted-foreground">
          Last signal: {incident.lastSignalAgo}
        </p>
        <Button type="button" size="sm" className="mt-3 w-full" onClick={onView}>
          View Incident
        </Button>
      </div>
    </aside>
  );
}

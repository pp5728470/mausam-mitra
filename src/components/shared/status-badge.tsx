import { cn } from "@/lib/utils";
import type { OperationalStatus } from "@/types/status";

const STATUS_COPY: Record<
  OperationalStatus,
  { label: string; className: string; pulse?: boolean }
> = {
  live: {
    label: "LIVE",
    className: "border-rain/25 bg-rain/10 text-rain",
    pulse: true,
  },
  active: {
    label: "ACTIVE",
    className: "border-weather/25 bg-weather/10 text-weather-secondary",
  },
  emerging: {
    label: "EMERGING",
    className: "border-warning/30 bg-warning/10 text-warning",
  },
  detected: {
    label: "DETECTED",
    className: "border-weather/20 bg-weather/8 text-weather-secondary",
    pulse: true,
  },
  subsiding: {
    label: "SUBSIDING",
    className: "border-white/10 bg-white/5 text-muted-foreground",
  },
  resolved: {
    label: "RESOLVED",
    className: "border-success/25 bg-success/10 text-success",
  },
  verified: {
    label: "VERIFIED",
    className: "border-success/30 bg-success/10 text-success",
  },
  under_review: {
    label: "UNDER REVIEW",
    className: "border-white/10 bg-white/5 text-muted-foreground",
  },
  high: {
    label: "HIGH",
    className: "border-warning/35 bg-warning/12 text-warning",
  },
  critical: {
    label: "CRITICAL",
    className: "border-critical/35 bg-critical/12 text-critical",
  },
};

type StatusBadgeProps = {
  status: OperationalStatus;
  className?: string;
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_COPY[status] ?? STATUS_COPY.active;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold tracking-[0.12em]",
        config.className,
        className,
      )}
    >
      {config.pulse ? (
        <span className="relative flex size-1.5" aria-hidden>
          <span className="status-ping absolute inset-0 rounded-full bg-current" />
          <span className="relative size-1.5 rounded-full bg-current" />
        </span>
      ) : (
        <span className="size-1.5 rounded-full bg-current" aria-hidden />
      )}
      {config.label}
    </span>
  );
}

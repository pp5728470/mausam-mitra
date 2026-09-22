/** Operational UI statuses used by StatusBadge and live indicators. */
export type OperationalStatus =
  | "live"
  | "active"
  | "emerging"
  | "detected"
  | "subsiding"
  | "resolved"
  | "verified"
  | "under_review"
  | "high"
  | "critical";

export const OPERATIONAL_STATUSES = [
  "live",
  "active",
  "emerging",
  "detected",
  "subsiding",
  "resolved",
  "verified",
  "under_review",
  "high",
  "critical",
] as const satisfies readonly OperationalStatus[];

/** @deprecated Prefer IncidentSeverity from @/types/incident */
export type IncidentSeverity = "low" | "moderate" | "high" | "critical";

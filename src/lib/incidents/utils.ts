import type {
  Incident,
  IncidentSeverity,
  IncidentStatus,
  IncidentTrend,
} from "@/types/incident";

export const SEVERITY_COLORS: Record<IncidentSeverity, string> = {
  critical: "#EF4444",
  high: "#F59E0B",
  medium: "#0EA5E9",
  low: "#93A4B8",
};

export const STATUS_LABELS: Record<IncidentStatus, string> = {
  detected: "DETECTED",
  emerging: "EMERGING",
  active: "ACTIVE",
  subsiding: "SUBSIDING",
  resolved: "RESOLVED",
};

export const SEVERITY_LABELS: Record<IncidentSeverity, string> = {
  critical: "CRITICAL",
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

export function trendLabel(trend: IncidentTrend): string {
  switch (trend) {
    case "rising":
      return "Rising";
    case "falling":
      return "Falling";
    default:
      return "Stable";
  }
}

export function trendArrow(trend: IncidentTrend): string {
  switch (trend) {
    case "rising":
      return "↑";
    case "falling":
      return "↓";
    default:
      return "→";
  }
}

export function shouldPulse(status: IncidentStatus): boolean {
  return (
    status === "detected" || status === "emerging" || status === "active"
  );
}

export function filterIncidents(
  incidents: Incident[],
  options: {
    severity?: IncidentSeverity | "all";
    layers?: {
      incidents?: boolean;
      verified?: boolean;
      emerging?: boolean;
    };
  },
): Incident[] {
  const severity = options.severity ?? "all";
  const layers = {
    incidents: true,
    verified: true,
    emerging: true,
    ...options.layers,
  };

  if (!layers.incidents) return [];

  return incidents.filter((incident) => {
    if (severity !== "all" && incident.severity !== severity) return false;
    if (
      !layers.verified &&
      (incident.status === "active" || incident.status === "resolved")
    ) {
      return false;
    }
    if (
      !layers.emerging &&
      (incident.status === "emerging" || incident.status === "detected")
    ) {
      return false;
    }
    return true;
  });
}

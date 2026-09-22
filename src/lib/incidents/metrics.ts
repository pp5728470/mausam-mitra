import type {
  CommandKpi,
  EmergingSignal,
  Incident,
  SituationSummary,
} from "@/types/incident";

const SEVERITY_RANK: Record<Incident["severity"], number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

const STATUS_RANK: Record<Incident["status"], number> = {
  active: 4,
  emerging: 3,
  detected: 2,
  subsiding: 1,
  resolved: 0,
};

/** Prefer genuine Phase 7 correlated incidents for intelligence surfaces. */
export function correlatedIncidents(incidents: Incident[]): Incident[] {
  return incidents.filter((i) => i.isCorrelated);
}

/**
 * Queue ordering:
 * 1) correlated first
 * 2) critical → high severity
 * 3) active → emerging
 * 4) medium → low
 * 5) recently updated
 * Zero-report / null-correlation never ahead of valid correlated.
 */
export function rankIncidentQueue(incidents: Incident[]): Incident[] {
  return [...incidents].sort((a, b) => {
    if (a.isCorrelated !== b.isCorrelated) {
      return a.isCorrelated ? -1 : 1;
    }
    const severityDelta = SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity];
    if (severityDelta !== 0) return severityDelta;
    const statusDelta = STATUS_RANK[b.status] - STATUS_RANK[a.status];
    if (statusDelta !== 0) return statusDelta;
    return Date.parse(b.lastSignalAt) - Date.parse(a.lastSignalAt);
  });
}

export function rankTopIncidents(
  incidents: Incident[],
  limit = 5,
): Incident[] {
  const pool = correlatedIncidents(incidents);
  const source = pool.length > 0 ? pool : incidents;
  return rankIncidentQueue(source).slice(0, limit);
}

export function deriveSituationSummary(
  incidents: Incident[],
): SituationSummary {
  const pool = correlatedIncidents(incidents);
  const activeIncidents = pool.filter((i) =>
    ["active", "emerging", "detected", "subsiding"].includes(i.status),
  ).length;
  const emerging = pool.filter(
    (i) => i.status === "emerging" || i.status === "detected",
  ).length;
  const underVerification = pool.filter(
    (i) => i.status === "subsiding",
  ).length;
  const critical = pool.filter((i) => i.severity === "critical").length;
  const rising = pool.filter((i) => i.trend === "rising").length;

  let trendLabel = "Stable nationwide operating picture";
  if (pool.length === 0) {
    trendLabel = "No correlated incidents in current window";
  } else if (rising >= 1 && critical >= 1) {
    trendLabel = "Critical correlated activity rising";
  } else if (rising >= 1) {
    trendLabel = "Rising activity in correlated clusters";
  } else if (emerging >= 1) {
    trendLabel = "Emerging correlated clusters requiring attention";
  } else if (critical >= 1) {
    trendLabel = "Critical correlated incidents under active watch";
  }

  return {
    activeIncidents,
    emerging,
    underVerification,
    critical,
    trendLabel,
  };
}

export function deriveCommandKpis(incidents: Incident[]): CommandKpi[] {
  const pool = correlatedIncidents(incidents);
  const summary = deriveSituationSummary(incidents);
  const active = pool.filter((i) => i.status === "active").length;
  const totalReports = pool.reduce(
    (sum, i) => sum + (i.linkedReportCount || i.evidence.reportCount),
    0,
  );

  return [
    {
      id: "kpi-active",
      label: "Correlated Incidents",
      value: summary.activeIncidents,
      displayValue: String(summary.activeIncidents).padStart(2, "0"),
      trend: "Phase 7 correlated clusters",
      support: "Excludes seeded/legacy without correlation",
      tone: "active",
    },
    {
      id: "kpi-emerging",
      label: "Emerging",
      value: summary.emerging,
      displayValue: String(summary.emerging).padStart(2, "0"),
      trend: "Detected / emerging correlated",
      support: "Rapid signal density",
      tone: "emerging",
    },
    {
      id: "kpi-verified",
      label: "Active",
      value: active,
      displayValue: String(active).padStart(2, "0"),
      trend: `${Math.round(
        (active / Math.max(summary.activeIncidents, 1)) * 100,
      )}% of open correlated`,
      support: "Sustained correlated activity",
      tone: "verified",
    },
    {
      id: "kpi-reports",
      label: "Linked Reports",
      value: totalReports,
      displayValue: totalReports.toLocaleString("en-IN"),
      trend: "Reports linked via incident_id",
      support: "Sum of correlated linked reports",
      tone: "reports",
    },
  ];
}

/**
 * Derive emerging-signal rows from correlated incident attributes.
 */
export function deriveEmergingSignals(
  incidents: Incident[],
  limit = 3,
): EmergingSignal[] {
  const pool = correlatedIncidents(incidents);
  return pool
    .filter(
      (i) =>
        i.status === "emerging" ||
        i.status === "detected" ||
        (i.trend === "rising" && i.severity !== "low"),
    )
    .sort((a, b) => b.evidence.reportCount - a.evidence.reportCount)
    .slice(0, limit)
    .map((incident, index) => ({
      id: `sig-${incident.id}`,
      city: incident.city,
      incidentId: incident.id,
      reportsDelta: Math.max(
        2,
        Math.round(incident.evidence.reportCount * (0.15 - index * 0.02)),
      ),
      windowLabel: "20 min",
    }));
}

import type {
  AnalyticsPoint,
  CommandFeedMeta,
  CommandKpi,
  EmergingSignal,
  SituationSummary,
} from "@/types/incident";
import { mockIncidents } from "@/lib/mock/incidents";

/**
 * Simulated analytics and operating-picture aggregates.
 * Swap these for FastAPI responses in a later phase.
 */
export const commandFeedMeta: CommandFeedMeta = {
  lastUpdatedIst: "10:42:18 IST",
  dataSourcesConnected: 12,
  signalsProcessed: 18426,
  signalsProcessedDisplay: "18,426",
  disclaimer: "SIMULATED OPERATING PICTURE",
};

export const situationSummary: SituationSummary = {
  activeIncidents: mockIncidents.filter((i) =>
    ["active", "emerging", "detected", "subsiding"].includes(i.status),
  ).length,
  emerging: mockIncidents.filter(
    (i) => i.status === "emerging" || i.status === "detected",
  ).length,
  underVerification: mockIncidents.filter((i) => i.status === "subsiding")
    .length,
  critical: mockIncidents.filter((i) => i.severity === "critical").length,
  trendLabel: "Rising activity across western and central India",
};

export const commandKpis: CommandKpi[] = [
  {
    id: "kpi-active",
    label: "Active Incidents",
    value: situationSummary.activeIncidents,
    displayValue: String(situationSummary.activeIncidents).padStart(2, "0"),
    trend: "+3 today",
    support: "Nationwide operating picture",
    tone: "active",
  },
  {
    id: "kpi-emerging",
    label: "Emerging",
    value: situationSummary.emerging,
    displayValue: String(situationSummary.emerging).padStart(2, "0"),
    trend: "+1 in last hour",
    support: "Rapid signal density",
    tone: "emerging",
  },
  {
    id: "kpi-verified",
    label: "Active",
    value: mockIncidents.filter((i) => i.status === "active").length,
    displayValue: String(
      mockIncidents.filter((i) => i.status === "active").length,
    ).padStart(2, "0"),
    trend: `${Math.round(
      (mockIncidents.filter((i) => i.status === "active").length /
        Math.max(situationSummary.activeIncidents, 1)) *
        100,
    )}% of open`,
    support: "Sustained correlated activity",
    tone: "verified",
  },
  {
    id: "kpi-reports",
    label: "Reports",
    value: 1284,
    displayValue: "1,284",
    trend: "+146 today",
    support: "Multi-source ingestion",
    tone: "reports",
  },
];

export const emergingSignals: EmergingSignal[] = [
  {
    id: "sig-pune",
    city: "Pune",
    incidentId: "inc-pune-waterlogging",
    reportsDelta: 42,
    windowLabel: "20 min",
  },
  {
    id: "sig-kolkata",
    city: "Kolkata",
    incidentId: "inc-kolkata-water",
    reportsDelta: 31,
    windowLabel: "20 min",
  },
  {
    id: "sig-mumbai",
    city: "Mumbai",
    incidentId: "inc-mumbai-rain",
    reportsDelta: 24,
    windowLabel: "20 min",
  },
];

export const mockAnalytics: AnalyticsPoint[] = [
  { hour: "00:00", signals: 42, verified: 8, emerging: 2 },
  { hour: "02:00", signals: 38, verified: 7, emerging: 1 },
  { hour: "04:00", signals: 31, verified: 6, emerging: 1 },
  { hour: "06:00", signals: 48, verified: 9, emerging: 2 },
  { hour: "08:00", signals: 67, verified: 11, emerging: 3 },
  { hour: "10:00", signals: 94, verified: 14, emerging: 4 },
  { hour: "12:00", signals: 112, verified: 16, emerging: 5 },
  { hour: "14:00", signals: 128, verified: 18, emerging: 5 },
  { hour: "16:00", signals: 141, verified: 19, emerging: 6 },
  { hour: "18:00", signals: 156, verified: 21, emerging: 5 },
  { hour: "20:00", signals: 138, verified: 20, emerging: 4 },
  { hour: "22:00", signals: 119, verified: 17, emerging: 3 },
];

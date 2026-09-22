import type { OperationalStatus } from "@/types/status";

export type IncidentSeverity = "low" | "medium" | "high" | "critical";

export type IncidentStatus =
  | "detected"
  | "emerging"
  | "active"
  | "subsiding"
  | "resolved";

export type IncidentTrend = "rising" | "stable" | "falling";

export type IncidentOrigin = "seeded" | "correlated" | "manual";

export type IncidentType =
  | "Flood"
  | "Waterlogging"
  | "Flood / Waterlogging"
  | "Heavy Rainfall"
  | "Extreme Heat"
  | "Severe Weather"
  | "Severe Storm";

export type IncidentSource =
  | "Citizen reports"
  | "Weather correlation"
  | "Nearby signals"
  | "Agency bulletin"
  | "Sensor network";

export type EvidenceSummary = {
  strength: number;
  reportCount: number;
  sources: IncidentSource[];
};

export type IncidentCoordinates = {
  lat: number;
  lng: number;
};

export type Incident = {
  id: string;
  code: string;
  title: string;
  locationLabel: string;
  city: string;
  state: string;
  type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  trend: IncidentTrend;
  origin: IncidentOrigin;
  isCorrelated: boolean;
  coordinates: IncidentCoordinates;
  evidence: EvidenceSummary;
  correlationScore: number | null;
  independentReportCount: number;
  linkedReportCount: number;
  radiusKm: number | null;
  timeWindowMinutes: number | null;
  lastSignalAgo: string;
  lastSignalAt: string;
  description: string;
};

/** Legacy alias kept for Phase 1 compatibility. */
export type WeatherIncident = {
  id: string;
  title: string;
  locationLabel: string;
  severity: "low" | "moderate" | "high" | "critical";
  status: OperationalStatus;
  detectedAt: string;
  verifiedAt: string | null;
};

export type HealthResponse = {
  status: "ok" | "degraded" | "down";
  service: string;
  timestamp: string;
};

export type ActivityEventKind =
  | "citizen_report"
  | "evidence_update"
  | "cluster_expanded"
  | "verification_completed"
  | "signal_spike";

export type ActivityEvent = {
  id: string;
  time: string;
  kind: ActivityEventKind;
  title: string;
  detail: string;
  incidentId?: string;
};

export type EmergingSignal = {
  id: string;
  city: string;
  incidentId: string;
  reportsDelta: number;
  windowLabel: string;
};

export type AnalyticsPoint = {
  hour: string;
  signals: number;
  verified: number;
  emerging: number;
};

export type SituationSummary = {
  activeIncidents: number;
  emerging: number;
  underVerification: number;
  critical: number;
  trendLabel: string;
};

export type CommandKpi = {
  id: string;
  label: string;
  value: number;
  displayValue: string;
  trend: string;
  support: string;
  tone: "active" | "emerging" | "verified" | "reports";
};

export type CommandFeedMeta = {
  lastUpdatedIst: string;
  dataSourcesConnected: number;
  signalsProcessed: number;
  signalsProcessedDisplay: string;
  disclaimer: string;
};

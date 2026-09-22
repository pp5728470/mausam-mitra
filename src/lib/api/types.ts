/**
 * Backend API types for Phase 3+ FastAPI contracts.
 * Map via src/lib/api/adapters/incidents.ts into Command Center Incident.
 */

export type ApiSourceType =
  | "CITIZEN"
  | "OFFICIAL"
  | "SENSOR"
  | "WEATHER_API"
  | "PUBLIC_FEED"
  | "OTHER";

export type ApiReportStatus = "NEW" | "PROCESSING" | "CORRELATED" | "REJECTED";

export type ApiIncidentStatus =
  | "DETECTED"
  | "EMERGING"
  | "ACTIVE"
  | "SUBSIDING"
  | "RESOLVED";

export type ApiIncidentSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type ApiIncidentTrend =
  | "RISING"
  | "STABLE"
  | "FALLING"
  | "INCREASING"
  | "IMPROVING";

export type ApiIncidentOrigin = "SEEDED" | "CORRELATED" | "MANUAL";

export type ApiHealthResponse = {
  status: string;
  service: string;
};

export type ApiPaginatedMeta = {
  total: number;
  limit: number;
  offset: number;
};

export type ApiPaginated<T> = {
  items: T[];
  meta: ApiPaginatedMeta;
};

export type ApiIncident = {
  id: string;
  incident_code: string;
  title: string;
  incident_type: string;
  description: string | null;
  severity: ApiIncidentSeverity;
  status: ApiIncidentStatus;
  trend: ApiIncidentTrend;
  origin?: ApiIncidentOrigin;
  latitude: number;
  longitude: number;
  evidence_score: number;
  report_count: number;
  linked_report_count?: number;
  correlation_score: number | null;
  independent_report_count: number;
  radius_km: number | null;
  time_window_minutes: number | null;
  first_detected_at: string;
  last_updated_at: string;
  created_at: string;
  updated_at: string;
  is_correlated?: boolean;
};

export type ApiNearbyIncident = ApiIncident & {
  distance_km: number;
};

export type ApiIncidentCreate = {
  title: string;
  incident_type: string;
  description?: string | null;
  severity: ApiIncidentSeverity;
  status: ApiIncidentStatus;
  trend?: ApiIncidentTrend;
  latitude: number;
  longitude: number;
  evidence_score?: number;
  report_count?: number;
  incident_code?: string | null;
  first_detected_at?: string | null;
};

export type ApiVerificationStatus =
  | "PENDING"
  | "UNDER_REVIEW"
  | "CORROBORATED"
  | "REJECTED"
  | "VERIFIED";

export type ApiVerificationRecommendation =
  | "NEEDS_REVIEW"
  | "CORROBORATED"
  | "HIGH_CONFIDENCE_REVIEW";

export type ApiVerificationDecision =
  | "VERIFIED"
  | "REJECTED"
  | "NEEDS_REVIEW";

export type ApiEvidenceType =
  | "LOCATION_CONSISTENCY"
  | "TIME_CONSISTENCY"
  | "WEATHER_CORRELATION"
  | "NEARBY_REPORTS"
  | "MEDIA_EVIDENCE"
  | "DUPLICATE_RISK"
  | "SOURCE_SIGNAL";

export type ApiReport = {
  id: string;
  source_type: ApiSourceType;
  source_name: string;
  title: string;
  description: string | null;
  latitude: number;
  longitude: number;
  reported_at: string | null;
  received_at: string;
  media_url: string | null;
  status: ApiReportStatus;
  classification: string | null;
  classification_confidence: number | null;
  
  // Phase 10: Intelligence
  classified_category: string | null;
  classifier_confidence: number | null;
  classification_explanation: string | null;
  classification_signals: Array<{ phrase: string; weight: number; source: string }> | null;
  classified_at: string | null;
  classifier_version: string | null;

  verification_status: ApiVerificationStatus;
  evidence_score: number | null;
  verification_recommendation: ApiVerificationRecommendation | null;
  verification_notes: string | null;
  verified_at: string | null;
  verified_by: string | null;
  incident_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ApiClassificationSignal = {
  phrase: string;
  weight: number;
  source: string;
};

export type ApiClassificationResponse = {
  report_id: string;
  classified_category: string;
  confidence: number;
  signals: ApiClassificationSignal[];
  explanation: string;
  classifier_version: string;
};

export type ApiReportCreate = {
  source_type: ApiSourceType;
  source_name: string;
  title: string;
  description: string;
  latitude: number;
  longitude: number;
  reported_at?: string | null;
  media_url?: string | null;
  /** Citizen-selected category — not AI classification. */
  classification?: string | null;
  incident_id?: string | null;
};

export type ApiEvidence = {
  id: string;
  report_id: string;
  evidence_type: ApiEvidenceType;
  title: string;
  description: string;
  score: number | null;
  confidence: number | null;
  source: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
};

export type ApiEvaluateResponse = {
  report: ApiReport;
  evidence: ApiEvidence[];
  evidence_score: number | null;
  evidence_coverage: string;
  verification_recommendation: ApiVerificationRecommendation;
};

export type ApiVerifyRequest = {
  decision: ApiVerificationDecision;
  notes?: string | null;
  verified_by?: string | null;
};

export type ApiVerifyResponse = {
  report: ApiReport;
  decision: ApiVerificationDecision;
  message: string;
};

export type ReportListParams = {
  status?: ApiReportStatus;
  source_type?: ApiSourceType;
  incident_id?: string;
  verification_status?: ApiVerificationStatus;
  limit?: number;
  offset?: number;
};

export type IncidentListParams = {
  status?: ApiIncidentStatus;
  severity?: ApiIncidentSeverity;
  incident_type?: string;
  limit?: number;
  offset?: number;
};

export type NearbyIncidentsParams = {
  latitude: number;
  longitude: number;
  radius_km?: number;
  limit?: number;
};

export type ApiCorrelationFactor = {
  name: string;
  score: number;
  weight: number;
  detail: string;
};

export type ApiCorrelateRequest = {
  latitude: number;
  longitude: number;
  radius_km?: number;
  window_minutes?: number;
  category?: string | null;
  create_incident?: boolean;
};

export type ApiCorrelateResponse = {
  correlation_score: number;
  threshold_met: boolean;
  factors: ApiCorrelationFactor[];
  report_count: number;
  independent_report_count: number;
  radius_km: number;
  time_window_minutes: number;
  centroid_latitude: number;
  centroid_longitude: number;
  incident_type: string;
  title: string;
  severity: ApiIncidentSeverity;
  status: ApiIncidentStatus;
  trend: ApiIncidentTrend;
  evidence_support: number;
  report_ids: string[];
  independent_report_ids: string[];
  notes: string[];
  incident: ApiIncident | null;
  message: string;
};

export type ApiTimelineEvent = {
  id: string;
  incident_id: string;
  event_type: string;
  title: string;
  detail: string | null;
  occurred_at: string;
  created_at: string;
};

export type ApiIncidentDetail = {
  incident: ApiIncident;
  reports: ApiReport[];
  timeline: ApiTimelineEvent[];
  correlation_explanation: ApiCorrelationFactor[] | null;
};

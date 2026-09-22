import type {
  ApiPaginated,
  ApiReport,
  ApiReportCreate,
  ApiReportStatus,
  ApiVerificationStatus,
} from "@/lib/api/types";
import { toNullableScore } from "@/lib/verification/format";

export type ReportListItem = {
  id: string;
  publicId: string;
  title: string;
  locationLabel: string;
  status: ApiReportStatus;
  sourceType: string;
  sourceName: string;
  receivedAt: string;
  receivedLabel: string;
  classification: string | null;
  verificationStatus: ApiVerificationStatus;
  evidenceScore: number | null;
  incidentId: string | null;
  hasMedia: boolean;
  latitude: number;
  longitude: number;
  description: string | null;
  mediaUrl: string | null;
  verificationRecommendation: string | null;
  verificationNotes: string | null;
  verifiedAt: string | null;
  verifiedBy: string | null;
  
  // Phase 10: Intelligence
  classifiedCategory: string | null;
  classifierConfidence: number | null;
  classificationExplanation: string | null;
  classificationSignals: Array<{ phrase: string; weight: number; source: string }> | null;
  classifiedAt: string | null;
  classifierVersion: string | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Runtime guard for paginated GET /api/v1/reports. */
export function isApiReportPage(
  value: unknown,
): value is ApiPaginated<ApiReport> {
  if (!isRecord(value)) return false;
  if (!Array.isArray(value.items) || !isRecord(value.meta)) return false;
  if (typeof value.meta.total !== "number") return false;
  return value.items.every(
    (item) =>
      isRecord(item) &&
      typeof item.id === "string" &&
      typeof item.title === "string" &&
      typeof item.latitude === "number" &&
      typeof item.longitude === "number" &&
      typeof item.received_at === "string",
  );
}

/** Short public reference — avoid dumping full UUIDs in the UI. */
export function toPublicReportId(id: string): string {
  const compact = id.replace(/-/g, "");
  return compact.slice(0, 8).toUpperCase();
}

export function formatCoord(value: number, digits = 4): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return value.toFixed(digits);
}

export function formatReceivedLabel(iso: string): string {
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return "—";
  return (
    new Date(t).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Asia/Kolkata",
    }) + " IST"
  );
}

export function mapApiReportToListItem(report: ApiReport): ReportListItem {
  return {
    id: report.id,
    publicId: toPublicReportId(report.id),
    title: report.title,
    locationLabel: `${formatCoord(report.latitude)}, ${formatCoord(report.longitude)}`,
    status: report.status,
    sourceType: report.source_type,
    sourceName: report.source_name,
    receivedAt: report.received_at,
    receivedLabel: formatReceivedLabel(report.received_at),
    classification: report.classification,
    verificationStatus: report.verification_status ?? "PENDING",
    evidenceScore: toNullableScore(report.evidence_score),
    incidentId: report.incident_id,
    hasMedia: Boolean(report.media_url),
    latitude: report.latitude,
    longitude: report.longitude,
    description: report.description,
    mediaUrl: report.media_url,
    verificationRecommendation: report.verification_recommendation,
    verificationNotes: report.verification_notes,
    verifiedAt: report.verified_at,
    verifiedBy: report.verified_by,
    classifiedCategory: report.classified_category,
    classifierConfidence: report.classifier_confidence,
    classificationExplanation: report.classification_explanation,
    classificationSignals: report.classification_signals,
    classifiedAt: report.classified_at,
    classifierVersion: report.classifier_version,
  };
}

export function buildCitizenReportPayload(input: {
  title: string;
  description: string;
  latitude: number;
  longitude: number;
  classification?: string | null;
  mediaUrl?: string | null;
  reportedAt?: string | null;
}): ApiReportCreate {
  return {
    source_type: "CITIZEN",
    source_name: "Citizen Report",
    title: input.title.trim(),
    description: input.description.trim(),
    latitude: input.latitude,
    longitude: input.longitude,
    classification: input.classification ?? null,
    media_url: input.mediaUrl ?? null,
    reported_at: input.reportedAt ?? new Date().toISOString(),
  };
}

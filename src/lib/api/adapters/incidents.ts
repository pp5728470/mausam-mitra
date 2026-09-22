import type {
  ApiIncident,
  ApiIncidentOrigin,
  ApiIncidentSeverity,
  ApiIncidentStatus,
  ApiIncidentTrend,
  ApiPaginated,
} from "@/lib/api/types";
import type {
  Incident,
  IncidentOrigin,
  IncidentSeverity,
  IncidentSource,
  IncidentStatus,
  IncidentTrend,
  IncidentType,
} from "@/types/incident";

const INCIDENT_TYPES: readonly IncidentType[] = [
  "Flood",
  "Waterlogging",
  "Flood / Waterlogging",
  "Heavy Rainfall",
  "Extreme Heat",
  "Severe Weather",
  "Severe Storm",
] as const;

/** City → state for seeded demo locations (API has no separate region fields). */
const CITY_STATE: Record<string, string> = {
  Bhopal: "Madhya Pradesh",
  Pune: "Maharashtra",
  Hinjewadi: "Maharashtra",
  Wakad: "Maharashtra",
  Mumbai: "Maharashtra",
  Ahmedabad: "Gujarat",
  Guwahati: "Assam",
  Chennai: "Tamil Nadu",
  Delhi: "Delhi",
  Hyderabad: "Telangana",
  Bengaluru: "Karnataka",
  Jaipur: "Rajasthan",
  Kolkata: "West Bengal",
  Patna: "Bihar",
  Kochi: "Kerala",
};

const DEFAULT_SOURCES: IncidentSource[] = [
  "Citizen reports",
  "Weather correlation",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isApiSeverity(value: unknown): value is ApiIncidentSeverity {
  return (
    value === "LOW" ||
    value === "MEDIUM" ||
    value === "HIGH" ||
    value === "CRITICAL"
  );
}

function isApiStatus(value: unknown): value is ApiIncidentStatus {
  return (
    value === "DETECTED" ||
    value === "EMERGING" ||
    value === "ACTIVE" ||
    value === "SUBSIDING" ||
    value === "RESOLVED" ||
    // Legacy values still accepted during transition
    value === "UNDER_REVIEW" ||
    value === "VERIFIED"
  );
}

function isApiTrend(value: unknown): value is ApiIncidentTrend {
  return (
    value === "RISING" ||
    value === "STABLE" ||
    value === "FALLING" ||
    value === "INCREASING" ||
    value === "IMPROVING"
  );
}

/** Runtime guard for a single FastAPI incident payload. */
export function isApiIncident(value: unknown): value is ApiIncident {
  if (!isRecord(value)) return false;
  return (
    typeof value.id === "string" &&
    typeof value.incident_code === "string" &&
    typeof value.title === "string" &&
    typeof value.incident_type === "string" &&
    isApiSeverity(value.severity) &&
    isApiStatus(value.status) &&
    isApiTrend(value.trend) &&
    typeof value.latitude === "number" &&
    typeof value.longitude === "number" &&
    typeof value.evidence_score === "number" &&
    typeof value.report_count === "number" &&
    typeof value.last_updated_at === "string"
  );
}

/** Runtime guard for paginated GET /api/v1/incidents. */
export function isApiIncidentPage(
  value: unknown,
): value is ApiPaginated<ApiIncident> {
  if (!isRecord(value)) return false;
  if (!Array.isArray(value.items) || !isRecord(value.meta)) return false;
  if (typeof value.meta.total !== "number") return false;
  return value.items.every(isApiIncident);
}

function mapSeverity(severity: ApiIncidentSeverity): IncidentSeverity {
  switch (severity) {
    case "CRITICAL":
      return "critical";
    case "HIGH":
      return "high";
    case "MEDIUM":
      return "medium";
    default:
      return "low";
  }
}

function mapStatus(status: ApiIncidentStatus | string): IncidentStatus {
  switch (status) {
    case "DETECTED":
      return "detected";
    case "EMERGING":
    case "UNDER_REVIEW":
      return "emerging";
    case "ACTIVE":
    case "VERIFIED":
      return "active";
    case "SUBSIDING":
      return "subsiding";
    case "RESOLVED":
      return "resolved";
    default:
      return "active";
  }
}

function mapTrend(trend: ApiIncidentTrend | string): IncidentTrend {
  switch (trend) {
    case "RISING":
    case "INCREASING":
      return "rising";
    case "FALLING":
    case "IMPROVING":
      return "falling";
    default:
      return "stable";
  }
}

function mapOrigin(origin: ApiIncidentOrigin | string | undefined): IncidentOrigin {
  switch (origin) {
    case "CORRELATED":
      return "correlated";
    case "MANUAL":
      return "manual";
    default:
      return "seeded";
  }
}

function mapType(raw: string): IncidentType {
  if ((INCIDENT_TYPES as readonly string[]).includes(raw)) {
    return raw as IncidentType;
  }
  const lower = raw.toLowerCase();
  if (lower.includes("flood") && lower.includes("water")) {
    return "Flood / Waterlogging";
  }
  if (lower.includes("storm")) return "Severe Storm";
  if (lower.includes("flood")) return "Flood";
  if (lower.includes("water")) return "Waterlogging";
  if (lower.includes("rain")) return "Heavy Rainfall";
  if (lower.includes("heat")) return "Extreme Heat";
  return "Severe Weather";
}

function cityFromTitle(title: string): string {
  const token = title.trim().split(/\s+/)[0] ?? "Unknown";
  return token;
}

function formatRelativeAgo(iso: string, now = Date.now()): string {
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return "—";
  const minutes = Math.max(0, Math.round((now - then) / 60_000));
  if (minutes < 1) return "just now";
  if (minutes === 1) return "1 min ago";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours === 1) return "1 hr ago";
  if (hours < 48) return `${hours} hr ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? "1 day ago" : `${days} days ago`;
}

/**
 * Normalize a FastAPI incident into the Command Center Incident shape.
 * Coordinates come only from the API latitude/longitude (PostGIS-backed).
 */
export function mapApiIncidentToIncident(api: ApiIncident): Incident {
  const city = cityFromTitle(api.title);
  const state = CITY_STATE[city] ?? "";
  const locationLabel = state ? `${city}, ${state}` : city;
  const origin = mapOrigin(api.origin);
  const linkedCount = api.linked_report_count ?? 0;
  const isCorrelated =
    api.is_correlated === true ||
    (origin === "correlated" &&
      api.correlation_score != null &&
      (api.independent_report_count ?? 0) >= 2 &&
      linkedCount >= 2);

  // Honest membership: correlated use linked counts; never invent correlation for legacy.
  const reportCount = isCorrelated
    ? linkedCount || api.report_count
    : linkedCount > 0
      ? linkedCount
      : api.report_count;

  return {
    id: api.id,
    code: api.incident_code,
    title: api.title,
    locationLabel,
    city,
    state,
    type: mapType(api.incident_type),
    severity: mapSeverity(api.severity),
    status: mapStatus(api.status),
    trend: mapTrend(api.trend),
    origin,
    isCorrelated,
    coordinates: {
      lat: api.latitude,
      lng: api.longitude,
    },
    evidence: {
      strength: api.evidence_score,
      reportCount,
      sources: DEFAULT_SOURCES,
    },
    correlationScore: isCorrelated ? (api.correlation_score ?? null) : null,
    independentReportCount: isCorrelated
      ? (api.independent_report_count ?? 0)
      : 0,
    linkedReportCount: linkedCount,
    radiusKm: isCorrelated ? (api.radius_km ?? null) : null,
    timeWindowMinutes: isCorrelated ? (api.time_window_minutes ?? null) : null,
    lastSignalAgo: formatRelativeAgo(api.last_updated_at),
    lastSignalAt: api.last_updated_at,
    description: api.description ?? "",
  };
}

export function mapApiIncidents(items: ApiIncident[]): Incident[] {
  return items.map(mapApiIncidentToIncident);
}

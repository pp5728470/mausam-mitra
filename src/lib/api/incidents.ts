import { apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type {
  ApiCorrelateRequest,
  ApiCorrelateResponse,
  ApiIncident,
  ApiIncidentCreate,
  ApiIncidentDetail,
  ApiNearbyIncident,
  ApiPaginated,
  ApiReport,
  ApiTimelineEvent,
  IncidentListParams,
  NearbyIncidentsParams,
} from "@/lib/api/types";

function toQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export async function getIncidents(
  params: IncidentListParams = {},
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiPaginated<ApiIncident>> {
  return apiRequest<ApiPaginated<ApiIncident>>(
    `${apiEndpoints.incidents}${toQuery(params)}`,
    { method: "GET", cache: "no-store", ...init },
  );
}

export async function getIncident(id: string): Promise<ApiIncident> {
  return apiRequest<ApiIncident>(`${apiEndpoints.incidents}/${id}`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function getIncidentDetail(id: string): Promise<ApiIncidentDetail> {
  return apiRequest<ApiIncidentDetail>(
    `${apiEndpoints.incidents}/${id}/detail`,
    { method: "GET", cache: "no-store" },
  );
}

export async function getIncidentReports(id: string): Promise<ApiReport[]> {
  return apiRequest<ApiReport[]>(`${apiEndpoints.incidents}/${id}/reports`, {
    method: "GET",
    cache: "no-store",
  });
}

export async function getIncidentTimeline(
  id: string,
): Promise<ApiTimelineEvent[]> {
  return apiRequest<ApiTimelineEvent[]>(
    `${apiEndpoints.incidents}/${id}/timeline`,
    { method: "GET", cache: "no-store" },
  );
}

export async function correlateIncidents(
  data: ApiCorrelateRequest,
): Promise<ApiCorrelateResponse> {
  return apiRequest<ApiCorrelateResponse>(
    `${apiEndpoints.incidents}/correlate`,
    { method: "POST", body: data },
  );
}

export async function createIncident(
  data: ApiIncidentCreate,
): Promise<ApiIncident> {
  return apiRequest<ApiIncident>(apiEndpoints.incidents, {
    method: "POST",
    body: data,
  });
}

export async function getNearbyIncidents(
  params: NearbyIncidentsParams,
): Promise<ApiNearbyIncident[]> {
  return apiRequest<ApiNearbyIncident[]>(
    `${apiEndpoints.incidentsNearby}${toQuery({
      latitude: params.latitude,
      longitude: params.longitude,
      radius_km: params.radius_km ?? 50,
      limit: params.limit ?? 50,
    })}`,
    { method: "GET", cache: "no-store" },
  );
}

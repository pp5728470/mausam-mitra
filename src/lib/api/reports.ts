import { apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type {
  ApiClassificationResponse,
  ApiEvaluateResponse,
  ApiEvidence,
  ApiPaginated,
  ApiReport,
  ApiReportCreate,
  ApiVerifyRequest,
  ApiVerifyResponse,
  ReportListParams,
} from "@/lib/api/types";

function toQuery(params: ReportListParams): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.source_type) search.set("source_type", params.source_type);
  if (params.incident_id) search.set("incident_id", params.incident_id);
  if (params.verification_status) {
    search.set("verification_status", params.verification_status);
  }
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export async function getReports(
  params: ReportListParams = {},
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiPaginated<ApiReport>> {
  return apiRequest<ApiPaginated<ApiReport>>(
    `${apiEndpoints.reports}${toQuery(params)}`,
    { method: "GET", cache: "no-store", ...init },
  );
}

export async function getReport(
  id: string,
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiReport> {
  return apiRequest<ApiReport>(`${apiEndpoints.reports}/${id}`, {
    method: "GET",
    cache: "no-store",
    ...init,
  });
}

/**
 * Create a raw report/signal. WRITE path — callers must never fake success
 * if this throws (no mock fallback).
 */
export async function createReport(
  data: ApiReportCreate,
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiReport> {
  return apiRequest<ApiReport>(apiEndpoints.reports, {
    method: "POST",
    body: data,
    ...init,
  });
}

export async function evaluateReport(
  id: string,
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiEvaluateResponse> {
  return apiRequest<ApiEvaluateResponse>(
    `${apiEndpoints.reports}/${id}/evaluate`,
    { method: "POST", ...init },
  );
}

export async function classifyReport(
  id: string,
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiClassificationResponse> {
  return apiRequest<ApiClassificationResponse>(
    `${apiEndpoints.reports}/${id}/classify`,
    { method: "POST", ...init },
  );
}

export async function getReportEvidence(
  id: string,
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiEvidence[]> {
  return apiRequest<ApiEvidence[]>(`${apiEndpoints.reports}/${id}/evidence`, {
    method: "GET",
    cache: "no-store",
    ...init,
  });
}

/**
 * Human verification decision. WRITE path — never fake success on failure.
 */
export async function verifyReport(
  id: string,
  data: ApiVerifyRequest,
  init: Omit<RequestInit, "body" | "method"> = {},
): Promise<ApiVerifyResponse> {
  return apiRequest<ApiVerifyResponse>(
    `${apiEndpoints.reports}/${id}/verify`,
    { method: "POST", body: data, ...init },
  );
}

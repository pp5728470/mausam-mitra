import { apiRequest } from "@/lib/api/client";
import { apiEndpoints } from "@/lib/api/endpoints";
import type { ApiHealthResponse } from "@/lib/api/types";

export async function getHealth(): Promise<ApiHealthResponse> {
  return apiRequest<ApiHealthResponse>(apiEndpoints.health, {
    method: "GET",
    cache: "no-store",
  });
}

/**
 * Connectivity probe for Phase 3+. Returns false when the API is offline
 * so the UI can keep serving mock data without throwing.
 */
export async function isBackendReachable(
  timeoutMs = 2500,
): Promise<boolean> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const health = await getHealth();
    return health.status === "ok";
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

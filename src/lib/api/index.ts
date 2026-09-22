/**
 * Phase 4 API surface — typed clients for Command Center + mock fallback.
 */
export { apiRequest, ApiError } from "@/lib/api/client";
export { apiEndpoints } from "@/lib/api/endpoints";
export { getHealth, isBackendReachable } from "@/lib/api/health";
export {
  correlateIncidents,
  createIncident,
  getIncident,
  getIncidentDetail,
  getIncidentReports,
  getIncidentTimeline,
  getIncidents,
  getNearbyIncidents,
} from "@/lib/api/incidents";
export {
  createReport,
  evaluateReport,
  getReport,
  getReportEvidence,
  getReports,
  verifyReport,
  classifyReport,
} from "./reports";
export {
  isApiIncident,
  isApiIncidentPage,
  mapApiIncidentToIncident,
  mapApiIncidents,
} from "@/lib/api/adapters/incidents";
export {
  buildCitizenReportPayload,
  isApiReportPage,
  mapApiReportToListItem,
  toPublicReportId,
} from "@/lib/api/adapters/reports";

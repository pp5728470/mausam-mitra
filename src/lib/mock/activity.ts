import type { ActivityEvent } from "@/types/incident";

/**
 * Simulated live activity stream for the command center.
 * Replace with WebSocket / GET /api/v1/activity later.
 */
export const mockActivity: ActivityEvent[] = [
  {
    id: "act-01",
    time: "10:42",
    kind: "citizen_report",
    title: "New citizen report",
    detail: "Pune, Maharashtra",
    incidentId: "inc-pune-waterlogging",
  },
  {
    id: "act-02",
    time: "10:40",
    kind: "evidence_update",
    title: "Incident evidence updated",
    detail: "Mumbai Heavy Rainfall",
    incidentId: "inc-mumbai-rain",
  },
  {
    id: "act-03",
    time: "10:38",
    kind: "cluster_expanded",
    title: "Incident cluster expanded",
    detail: "Pune Waterlogging",
    incidentId: "inc-pune-waterlogging",
  },
  {
    id: "act-04",
    time: "10:35",
    kind: "verification_completed",
    title: "Analyst verification completed",
    detail: "Ahmedabad Heat Stress",
    incidentId: "inc-ahmedabad-heat",
  },
  {
    id: "act-05",
    time: "10:33",
    kind: "signal_spike",
    title: "Signal density spike detected",
    detail: "Kolkata Waterlogging",
    incidentId: "inc-kolkata-water",
  },
  {
    id: "act-06",
    time: "10:29",
    kind: "citizen_report",
    title: "New citizen report",
    detail: "Guwahati, Assam",
    incidentId: "inc-guwahati-flood",
  },
  {
    id: "act-07",
    time: "10:26",
    kind: "evidence_update",
    title: "Evidence strength revised",
    detail: "Patna River Rise · 85%",
    incidentId: "inc-patna-flood",
  },
];

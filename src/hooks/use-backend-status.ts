"use client";

import { useEffect, useState } from "react";

import { isBackendReachable } from "@/lib/api/health";

export type BackendLinkStatus = "checking" | "online" | "offline";

/**
 * Soft connectivity probe. Prefer useIncidents().source for Command Center
 * data-source badges (Phase 4) to avoid duplicate status indicators.
 */
export function useBackendStatus(pollMs = 60_000): BackendLinkStatus {
  const [status, setStatus] = useState<BackendLinkStatus>("checking");

  useEffect(() => {
    let cancelled = false;

    const probe = async () => {
      const online = await isBackendReachable();
      if (!cancelled) setStatus(online ? "online" : "offline");
    };

    void probe();
    const id = window.setInterval(probe, pollMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [pollMs]);

  return status;
}

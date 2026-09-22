"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  isApiIncidentPage,
  mapApiIncidents,
} from "@/lib/api/adapters/incidents";
import { ApiError, getIncidents } from "@/lib/api";
import { mockIncidents } from "@/lib/mock/incidents";
import type { Incident } from "@/types/incident";

export type IncidentDataSource = "api" | "mock";

export type UseIncidentsResult = {
  incidents: Incident[];
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  source: IncidentDataSource;
  /** True after the first successful or fallback resolution. */
  hasResolved: boolean;
  refresh: () => void;
};

const FETCH_TIMEOUT_MS = 8_000;

function logDev(message: string, detail?: unknown) {
  if (process.env.NODE_ENV === "development") {
    if (detail === undefined) {
      console.warn(`[useIncidents] ${message}`);
    } else {
      console.warn(`[useIncidents] ${message}`, detail);
    }
  }
}

async function fetchIncidentsFromApi(
  signal: AbortSignal,
): Promise<Incident[]> {
  const page = await getIncidents(
    { limit: 200, offset: 0 },
    { signal },
  );

  if (!isApiIncidentPage(page)) {
    throw new Error("Malformed incidents response from API");
  }

  return mapApiIncidents(page.items);
}

/**
 * Load Command Center incidents from FastAPI with graceful mock fallback.
 * Does not flash mock data before the first request settles.
 */
export function useIncidents(): UseIncidentsResult {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<IncidentDataSource>("mock");
  const [hasResolved, setHasResolved] = useState(false);
  const [refreshToken, setRefreshToken] = useState(0);
  const hasResolvedRef = useRef(false);

  const refresh = useCallback(() => {
    setRefreshToken((n) => n + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(
      () => controller.abort(),
      FETCH_TIMEOUT_MS,
    );
    const isInitial = !hasResolvedRef.current;

    if (isInitial) {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }

    void (async () => {
      try {
        const mapped = await fetchIncidentsFromApi(controller.signal);
        if (controller.signal.aborted) return;
        setIncidents(mapped);
        setSource("api");
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;

        const message =
          err instanceof ApiError
            ? `HTTP ${err.status}: ${err.message}`
            : err instanceof Error
              ? err.message
              : "Unknown incidents fetch error";

        logDev("Falling back to mockIncidents", message);

        setIncidents(mockIncidents);
        setSource("mock");
        setError(message);
      } finally {
        if (!controller.signal.aborted) {
          hasResolvedRef.current = true;
          setHasResolved(true);
          setIsLoading(false);
          setIsRefreshing(false);
        }
        window.clearTimeout(timer);
      }
    })();

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [refreshToken]);

  return {
    incidents,
    isLoading,
    isRefreshing,
    error,
    source,
    hasResolved,
    refresh,
  };
}

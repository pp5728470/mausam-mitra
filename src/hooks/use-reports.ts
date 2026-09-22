"use client";

import { useCallback, useEffect, useState } from "react";

import {
  mapApiReportToListItem,
  type ReportListItem,
} from "@/lib/api/adapters/reports";
import { ApiError, getReports } from "@/lib/api";
import type { ApiReportStatus, ApiSourceType } from "@/lib/api/types";

export type UseReportsResult = {
  reports: ReportListItem[];
  total: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
};

/**
 * Read-side reports list. Failures surface as errors (no silent fake writes).
 * Empty list on failure is OK for display; create path never uses this as success.
 */
export function useReports(options?: {
  sourceType?: ApiSourceType;
  status?: ApiReportStatus;
  limit?: number;
}): UseReportsResult {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState(0);

  const refresh = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setToken((n) => n + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8_000);

    void (async () => {
      try {
        const page = await getReports(
          {
            limit: options?.limit ?? 30,
            offset: 0,
            source_type: options?.sourceType,
            status: options?.status,
          },
          { signal: controller.signal },
        );
        if (controller.signal.aborted) return;
        setReports(page.items.map(mapApiReportToListItem));
        setTotal(page.meta.total);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof ApiError
            ? `HTTP ${err.status}: ${err.message}`
            : err instanceof Error
              ? err.message
              : "Unable to load reports";
        setError(message);
        setReports([]);
        setTotal(0);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
        window.clearTimeout(timer);
      }
    })();

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [token, options?.limit, options?.sourceType, options?.status]);

  return { reports, total, isLoading, error, refresh };
}

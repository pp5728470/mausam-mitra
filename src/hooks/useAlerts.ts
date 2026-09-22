"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAlerts, markAlertRead, markAlertAcknowledged, AlertListResponse } from "@/lib/api/alerts";

export function useAlerts(options?: { pollingInterval?: number; limit?: number; offset?: number; status?: string }) {
  const [data, setData] = useState<AlertListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const pollingInterval = options?.pollingInterval ?? 60000;
  const isVisible = useRef(true);
  
  const refresh = useCallback(() => {
    setRefreshTrigger(v => v + 1);
  }, []);

  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisible.current = document.visibilityState === 'visible';
      if (isVisible.current) {
        refresh();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [refresh]);

  useEffect(() => {
    const controller = new AbortController();
    let timeoutId: number;

    const fetchAlerts = async () => {
      if (!isVisible.current) {
        timeoutId = window.setTimeout(fetchAlerts, pollingInterval);
        return;
      }
      try {
        const response = await getAlerts({
          limit: options?.limit,
          offset: options?.offset,
          status: options?.status,
        }, { signal: controller.signal });
        
        setData(response);
        setIsError(false);
      } catch {
        if (!controller.signal.aborted) {
          setIsError(true);
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
          timeoutId = window.setTimeout(fetchAlerts, pollingInterval);
        }
      }
    };

    fetchAlerts();

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [options?.limit, options?.offset, options?.status, pollingInterval, refreshTrigger]);

  const [isPendingRead, setIsPendingRead] = useState(false);
  const [isPendingAck, setIsPendingAck] = useState(false);

  const markRead = {
    mutate: async (id: string) => {
      setIsPendingRead(true);
      try {
        await markAlertRead(id);
        refresh();
      } finally {
        setIsPendingRead(false);
      }
    },
    isPending: isPendingRead
  };

  const markAcknowledged = {
    mutate: async (id: string) => {
      setIsPendingAck(true);
      try {
        await markAlertAcknowledged(id);
        refresh();
      } finally {
        setIsPendingAck(false);
      }
    },
    isPending: isPendingAck
  };

  return {
    data,
    isLoading,
    isError,
    markRead,
    markAcknowledged,
    refresh
  };
}

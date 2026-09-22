import { useCallback, useEffect, useState } from "react";
import { analyticsApi } from "@/lib/api/analytics";
import type { 
  AnalyticsOverview, 
  AnalyticsTrends, 
  AnalyticsCategories, 
  AnalyticsSeverity, 
  AnalyticsGeography, 
  AnalyticsWeather 
} from "@/lib/api/analytics";

export function useAnalytics(days: number = 7) {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null);
  const [categories, setCategories] = useState<AnalyticsCategories | null>(null);
  const [severity, setSeverity] = useState<AnalyticsSeverity | null>(null);
  const [geography, setGeography] = useState<AnalyticsGeography | null>(null);
  const [weather, setWeather] = useState<AnalyticsWeather | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [
        overviewData,
        trendsData,
        categoriesData,
        severityData,
        geographyData,
        weatherData
      ] = await Promise.all([
        analyticsApi.getOverview(days),
        analyticsApi.getTrends(),
        analyticsApi.getCategories(days),
        analyticsApi.getSeverity(days),
        analyticsApi.getGeography(days),
        analyticsApi.getWeather(days)
      ]);

      setOverview(overviewData);
      setTrends(trendsData);
      setCategories(categoriesData);
      setSeverity(severityData);
      setGeography(geographyData);
      setWeather(weatherData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to load analytics"));
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    // Avoid synchronous state updates in effect
    const load = async () => {
      await fetchAll();
    };
    load();
  }, [fetchAll]);

  const refresh = useCallback(() => {
    setIsLoading(true);
    fetchAll();
  }, [fetchAll]);

  return {
    overview,
    trends,
    categories,
    severity,
    geography,
    weather,
    isLoading,
    error,
    refresh
  };
}

import { apiRequest } from "@/lib/api/client";

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface SeverityCount {
  severity: string;
  count: number;
}

export interface AnalyticsOverview {
  total_reports: number;
  reports_last_24h: number;
  reports_last_7d: number;
  new_reports: number;
  under_review_reports: number;
  verified_reports: number;
  rejected_reports: number;
  pending_reports: number;
  total_incidents: number;
  correlated_incidents: number;
  seeded_incidents: number;
  manual_incidents: number;
  active_incidents: number;
  emerging_incidents: number;
  critical_incidents: number;
  high_severity_incidents: number;
  rising_incidents: number;
  linked_reports: number;
  unlinked_reports: number;
  correlation_rate: number;
  classified_reports: number;
  unclassified_reports: number;
  average_classifier_confidence: number | null;
}

export interface AnalyticsTrends {
  reports_24h: TimeSeriesPoint[];
  reports_7d: TimeSeriesPoint[];
  reports_30d: TimeSeriesPoint[];
}

export interface AnalyticsCategories {
  distribution: CategoryCount[];
}

export interface AnalyticsSeverity {
  distribution: SeverityCount[];
}

export interface GeographicPoint {
  latitude: number;
  longitude: number;
  report_count: number;
  incident_count: number;
}

export interface AnalyticsGeography {
  points: GeographicPoint[];
}

export interface AnalyticsWeather {
  observation_count: number;
  average_temperature: number | null;
  maximum_temperature: number | null;
  average_humidity: number | null;
  average_wind_speed: number | null;
}

export const analyticsApi = {
  getOverview: (days: number = 30): Promise<AnalyticsOverview> =>
    apiRequest(`/api/v1/analytics/overview?days=${days}`),
    
  getTrends: (): Promise<AnalyticsTrends> =>
    apiRequest(`/api/v1/analytics/trends`),
    
  getCategories: (days: number = 30): Promise<AnalyticsCategories> =>
    apiRequest(`/api/v1/analytics/categories?days=${days}`),
    
  getSeverity: (days: number = 30): Promise<AnalyticsSeverity> =>
    apiRequest(`/api/v1/analytics/severity?days=${days}`),
    
  getGeography: (days: number = 30): Promise<AnalyticsGeography> =>
    apiRequest(`/api/v1/analytics/geography?days=${days}`),
    
  getWeather: (days: number = 30): Promise<AnalyticsWeather> =>
    apiRequest(`/api/v1/analytics/weather?days=${days}`),
};

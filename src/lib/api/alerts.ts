import { apiRequest } from './client';


export interface Alert {
  id: string;
  alert_type: string;
  severity: string | null;
  title: string;
  message: string;
  status: 'UNREAD' | 'READ' | 'ACKNOWLEDGED';
  recipient_scope: string;
  incident_id: string | null;
  report_id: string | null;
  metadata_payload: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  read_at: string | null;
  acknowledged_at: string | null;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  unread_count: number;
}

export const getAlerts = async (
  params?: { status?: string; limit?: number; offset?: number },
  init?: RequestInit
): Promise<AlertListResponse> => {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit !== undefined) searchParams.set('limit', params.limit.toString());
  if (params?.offset !== undefined) searchParams.set('offset', params.offset.toString());
  
  const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
  return apiRequest<AlertListResponse>(`/api/v1/alerts${query}`, init);
};

export const markAlertRead = async (id: string, init?: RequestInit): Promise<Alert> => {
  return apiRequest<Alert>(`/api/v1/alerts/${id}/read`, {
    ...init,
    method: 'PATCH',
  });
};

export const markAlertAcknowledged = async (id: string, init?: RequestInit): Promise<Alert> => {
  return apiRequest<Alert>(`/api/v1/alerts/${id}/acknowledge`, {
    ...init,
    method: 'PATCH',
  });
};

export const getUnreadCount = async (init?: RequestInit): Promise<{ unread_count: number }> => {
  return apiRequest<{ unread_count: number }>(`/api/v1/alerts/unread-count`, init);
};

export const getAlertById = async (id: string, init?: RequestInit): Promise<Alert> => {
  return apiRequest<Alert>(`/api/v1/alerts/${id}`, init);
};

import { apiRequest } from "../../../core/api/client";

const BASE = "/detection/behavior";

export const behavioralService = {
  summary: () => apiRequest(`${BASE}/summary`),
  activity: (period = "7d") => apiRequest(`${BASE}/activity?period=${encodeURIComponent(period)}`),
  anomalies: () => apiRequest(`${BASE}/anomalies`),
};

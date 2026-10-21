import { apiRequest } from "../../../core/api/client";

const BASE = "/detection/risk";

export const riskService = {
  summary: () => apiRequest(`${BASE}/summary`),
  distribution: () => apiRequest(`${BASE}/distribution`),
  factors: () => apiRequest(`${BASE}/factors`),
};

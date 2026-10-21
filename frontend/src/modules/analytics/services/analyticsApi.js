import { apiDownload, apiRequest } from "../../../core/api/client";

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  return search.size ? `?${search}` : "";
}

export const analyticsApi = {
  get: (path, params) => apiRequest(`/analytics${path}${query(params)}`),
  async export(params) {
    const format = params?.format === "json" ? "json" : "csv";
    await apiDownload(`/analytics/export${query(params)}`, `analytics.${format}`);
  },
};

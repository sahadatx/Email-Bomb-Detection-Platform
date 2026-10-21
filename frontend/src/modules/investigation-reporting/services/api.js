import { apiDownload, apiRequest } from "../../../core/api/client";

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  return search.size ? `?${search}` : "";
}

export const investigationApi = {
  get: (path, params) => apiRequest(`${path}${query(params)}`),
  post: (path, body) => apiRequest(path, { method: "POST", body }),
  patch: (path, body) => apiRequest(path, { method: "PATCH", body }),
  delete: (path) => apiRequest(path, { method: "DELETE" }),
  async download(path, filename) {
    await apiDownload(path, filename);
  },
};

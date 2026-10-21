import { apiDownload, apiRequest } from "../../../core/api/client";

export function queryString(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, String(value));
  });
  return query.size ? `?${query}` : "";
}

export const get = (path, params) => apiRequest(`${path}${queryString(params)}`);
export const post = (path, body) => apiRequest(path, { method: "POST", body });
export const patch = (path, body) => apiRequest(path, { method: "PATCH", body });
export const download = (path, filename) => apiDownload(path, filename);

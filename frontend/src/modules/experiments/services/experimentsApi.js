import { apiRequest } from "../../../core/api/client";

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== "") search.set(key, String(value)); });
  return search.size ? `?${search}` : "";
}
export const experimentsApi = {
  get: (path, params) => apiRequest(`/experiments${path}${query(params)}`),
  post: (path, body = {}) => apiRequest(`/experiments${path}`, { method: "POST", body }),
  patch: (path, body) => apiRequest(`/experiments${path}`, { method: "PATCH", body }),
  delete: (path) => apiRequest(`/experiments${path}`, { method: "DELETE" }),
};

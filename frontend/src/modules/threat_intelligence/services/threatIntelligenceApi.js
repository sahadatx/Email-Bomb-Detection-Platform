import { apiRequest, apiDownload } from "../../../core/api/client";

const query = (params = {}) => {
  const values = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "")
      values.set(key, String(value));
  });
  return values.size ? `?${values}` : "";
};
const root = "/threat-intelligence";
export const threatIntelligenceApi = {
  get: (path, params) => apiRequest(`${root}${path}${query(params)}`),
  post: (path, body = {}) =>
    apiRequest(`${root}${path}`, { method: "POST", body }),
  patch: (path, body) =>
    apiRequest(`${root}${path}`, { method: "PATCH", body }),
  delete: (path) => apiRequest(`${root}${path}`, { method: "DELETE" }),
  download: (path, params, filename) =>
    apiDownload(`${root}${path}${query(params)}`, filename),
};

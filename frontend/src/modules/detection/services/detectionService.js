import { apiRequest } from "../../../core/api/client";

const BASE = "/detection";
const qs = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  return query.size ? `?${query}` : "";
};

export const detectionService = {
  overview: (period = "7d") => apiRequest(`${BASE}/summary${qs({ period })}`),
  list: (params) => apiRequest(`${BASE}${qs(params)}`),
  detail: (id) => apiRequest(`${BASE}/${id}`),
  report: (id) => apiRequest(`${BASE}/${id}/report`),
  emails: (search) => apiRequest(`${BASE}/emails${qs({ search })}`),
  activeModel: () => apiRequest(`${BASE}/active-model`),
  activeModels: () => apiRequest(`${BASE}/active-models`),
  create: (payload) => apiRequest(BASE, { method: "POST", body: payload }),
  createRaw: (payload) => apiRequest(`${BASE}/raw`, { method: "POST", body: payload }),
  createBatch: (payload) => apiRequest(`${BASE}/batch`, { method: "POST", body: payload }),
  upload: (file, options) => {
    const form = new FormData();
    form.append("file", file);
    Object.entries(options).forEach(([key, value]) => form.append(key, String(value)));
    return apiRequest(`${BASE}/upload`, { method: "POST", body: form });
  },
  uploadBatch: (files, options) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    Object.entries(options).forEach(([key, value]) => form.append(key, String(value)));
    return apiRequest(`${BASE}/batch/upload`, { method: "POST", body: form });
  },
};

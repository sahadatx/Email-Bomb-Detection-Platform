import { investigationApi as api } from "./api";

const BASE = "/evidence";
function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  return search.size ? `?${search}` : "";
}

export const evidenceService = {
  list: (params) => api.get(BASE, params),
  detail: (id) => api.get(`${BASE}/${id}`),
  create: (payload) => api.post(BASE, payload),
  update: (id, payload) => api.patch(`${BASE}/${id}`, payload),
  review: (id, payload) => api.post(`${BASE}/${id}/review`, payload),
  export: (params) => api.download(`${BASE}/export${query(params)}`, "evidence-export.json"),
};

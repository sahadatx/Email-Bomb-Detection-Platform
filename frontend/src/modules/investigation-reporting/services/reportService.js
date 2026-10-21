import { investigationApi as api } from "./api";

const BASE = "/reports";
export const reportService = {
  list: (params) => api.get(BASE, params),
  detail: (id) => api.get(`${BASE}/${id}`),
  audit: (id) => api.get(`${BASE}/${id}/audit`),
  create: (payload) => api.post(BASE, payload),
  preview: (payload) => api.post(`${BASE}/preview`, payload),
  update: (id, payload) => api.patch(`${BASE}/${id}`, payload),
  generate: (id) => api.post(`${BASE}/${id}/generate`, {}),
  duplicate: (id) => api.post(`${BASE}/${id}/duplicate`, {}),
  archive: (id) => api.post(`${BASE}/${id}/archive`, {}),
  download: (id, format = "json") => api.download(`${BASE}/${id}/download`, `report-${id}.${format}`),
};

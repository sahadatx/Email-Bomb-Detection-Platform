import { investigationApi as api } from "./api";

const BASE = "/explainability";
export const explainabilityService = {
  list: (params) => api.get(BASE, params),
  detail: (id) => api.get(`${BASE}/${id}`),
  addNote: (id, payload) => api.post(`${BASE}/${id}/notes`, payload),
  updateNote: (id, payload) => api.patch(`${BASE}/notes/${id}`, payload),
  deleteNote: (id) => api.delete(`${BASE}/notes/${id}`),
  export: (id) => api.download(`${BASE}/${id}/export`, `explanation-${id}.json`),
};

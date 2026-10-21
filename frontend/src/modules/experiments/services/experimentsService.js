import { experimentsApi } from "./experimentsApi";

export const experimentsService = {
  options: () => experimentsApi.get("/options"),
  list: (params) => experimentsApi.get("", params),
  summary: () => experimentsApi.get("/summary"),
  create: (body) => experimentsApi.post("", body),
  detail: (id) => experimentsApi.get(`/${encodeURIComponent(id)}`),
  update: (id, body) => experimentsApi.patch(`/${encodeURIComponent(id)}`, body),
  remove: (id) => experimentsApi.delete(`/${encodeURIComponent(id)}`),
  runs: (id) => experimentsApi.get(`/${encodeURIComponent(id)}/runs`),
  startRun: (id) => experimentsApi.post(`/${encodeURIComponent(id)}/runs`),
  run: (runId) => experimentsApi.get(`/runs/${encodeURIComponent(runId)}`),
  logs: (runId) => experimentsApi.get(`/runs/${encodeURIComponent(runId)}/logs`),
  compare: (experiment_ids) => experimentsApi.post("/compare", { experiment_ids }),
};

import { download, get, queryString } from "./api";

export const auditService = {
  list: (params) => get("/audit", params),
  summary: (params) => get("/audit/summary", params),
  options: () => get("/audit/options"),
  detail: (id) => get(`/audit/${id}`),
  export: (params) => download(`/audit/export${queryString(params)}`, `audit-events.${params.format || "csv"}`),
};

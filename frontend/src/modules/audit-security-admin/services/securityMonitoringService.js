import { get, patch, post } from "./api";

export const securityMonitoringService = {
  summary: () => get("/security-monitoring/summary"),
  options: () => get("/security-monitoring/options"),
  events: (params) => get("/security-monitoring/events", params),
  event: (id) => get(`/security-monitoring/events/${id}`),
  transitionEvent: (id, payload) => patch(`/security-monitoring/events/${id}`, payload),
  createAlertFromEvent: (id) => post(`/security-monitoring/events/${id}/alerts`, {}),
  alerts: (params) => get("/security-monitoring/alerts", params),
  analysts: () => get("/security-monitoring/analysts"),
  alert: (id) => get(`/security-monitoring/alerts/${id}`),
  transitionAlert: (id, payload) => patch(`/security-monitoring/alerts/${id}`, payload),
  rules: (params) => get("/security-monitoring/rules", params),
  createRule: (payload) => post("/security-monitoring/rules", payload),
  updateRule: (id, payload) => patch(`/security-monitoring/rules/${id}`, payload),
};

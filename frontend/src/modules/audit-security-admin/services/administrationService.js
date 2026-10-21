import { get, patch } from "./api";

export const administrationService = {
  settings: () => get("/administration/settings"),
  updateSetting: (key, payload) => patch(`/administration/settings/${key}`, payload),
  settingHistory: (key, params) => get(`/administration/settings/${key}/history`, params),
  jobs: (params) => get("/administration/jobs", params),
  job: (id) => get(`/administration/jobs/${id}`),
  health: () => get("/administration/health"),
};

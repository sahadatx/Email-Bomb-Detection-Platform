import { apiRequest } from "../../../core/api/client";

const BASE = "/detection/settings";

export const detectionSettingsService = {
  get: () => apiRequest(BASE),
  update: (payload) => apiRequest(BASE, { method: "PATCH", body: payload }),
};

import { apiRequest } from "../../../core/api/client";

export const settingsApi = {
  getOverview: (options) => apiRequest("/settings", options),
  getCategory: (category, options) => apiRequest(`/settings/${category}`, options),
  updateCategory: (category, values, reason, options) => apiRequest(`/settings/${category}`, {
    method: "PUT",
    body: { values, reason },
    ...options,
  }),
};

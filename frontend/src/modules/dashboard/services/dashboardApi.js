import { apiRequest } from "../../../core/api/client";

function queryString(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === "" || value === null || value === undefined) return;
    // datetime-local values are in the analyst's local timezone. Send their
    // absolute UTC instants so the backend can aggregate a consistent window.
    if (
      (key === "start_date" || key === "end_date") &&
      typeof value === "string" &&
      !/[zZ]|[+-]\d\d:\d\d$/.test(value)
    ) {
      const date = new Date(value);
      if (!Number.isNaN(date.getTime())) params.set(key, date.toISOString());
      return;
    }
    params.set(key, value);
  });
  return params.toString();
}

export const dashboardApi = {
  getOverview(filters, options = {}) {
    const query = queryString(filters);
    return apiRequest(
      `/dashboard/overview${query ? `?${query}` : ""}`,
      options,
    );
  },
};

export { queryString };

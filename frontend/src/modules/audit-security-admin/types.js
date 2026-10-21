export const SEVERITIES = ["critical", "high", "medium", "low"];
export const EVENT_STATUSES = ["new", "reviewed", "investigating"];
export const ALERT_STATUSES = ["open", "investigating", "resolved"];
export const ADMIN_TABS = { monitoring: ["Events", "Alerts", "Monitoring Rules"], administration: ["Overview", "Settings", "Background Jobs", "Health"] };

export function displayDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

export function errorMessage(error) {
  return error?.message || "The request could not be completed.";
}

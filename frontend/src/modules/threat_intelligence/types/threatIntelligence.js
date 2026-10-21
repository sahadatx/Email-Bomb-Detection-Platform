export const THREAT_SEVERITIES = ["low", "medium", "high", "critical"];
export const INDICATOR_TYPES = ["ip", "domain", "url", "hash", "email"];
export const FEED_TYPES = ["stix_taxii", "csv", "json", "api", "internal"];
export const MATCH_STATUSES = ["new", "reviewed", "investigating", "resolved"];
export const DEFAULT_TIME_RANGE = "30d";
export const errorMessage = (error) =>
  error?.message || error?.detail || "The request could not be completed.";
export const displayDate = (date) =>
  date ? new Date(date).toLocaleString() : "—";
export const displayLabel = (value = "") =>
  value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export const EXPERIMENT_STATUSES = ["queued", "running", "completed", "failed", "cancelled", "draft"];
export const statusLabel = (status = "draft") => status.charAt(0).toUpperCase() + status.slice(1);
export const formatPercent = (value) => value == null ? "—" : `${(Number(value) * 100).toFixed(2)}%`;
export const formatDate = (value) => value ? new Date(value).toLocaleString() : "—";
export const errorText = (error) => error?.message || error?.detail?.message || "The request could not be completed.";

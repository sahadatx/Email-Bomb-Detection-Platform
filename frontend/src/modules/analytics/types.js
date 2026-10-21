export const ANALYTICS_RANGES = [
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
  { value: "custom", label: "Custom range" },
];

export const DEFAULT_ANALYTICS_FILTERS = {
  time_range: "30d",
  classification: "",
  risk_level: "",
  model_definition_id: "",
  from_date: "",
  to_date: "",
};

export const formatMetric = (value, digits = 1) =>
  value == null ? "—" : `${Number(value).toFixed(digits)}%`;

export const formatCount = (value) => Number(value || 0).toLocaleString();

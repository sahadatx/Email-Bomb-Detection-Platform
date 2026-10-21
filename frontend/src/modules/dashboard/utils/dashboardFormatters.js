export const numberFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 0,
});

export function formatNumber(value) {
  return Number.isFinite(Number(value))
    ? numberFormat.format(Number(value))
    : "—";
}

export function formatDate(
  value,
  options = { dateStyle: "medium", timeStyle: "short" },
) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Not available"
    : new Intl.DateTimeFormat(undefined, options).format(date);
}

export function statusLabel(status = "unknown") {
  return String(status)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function metricValue(metric) {
  return metric?.available === false
    ? "Unavailable"
    : formatNumber(metric?.value);
}

export function clampPercent(value) {
  const n = Number(value) || 0;
  return Math.max(0, Math.min(100, n));
}

const DEFAULT_MESSAGE = "The request could not be completed. Please try again.";

function text(value) {
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function formatValidationItem(item) {
  if (!item || typeof item !== "object") return text(item);
  const location = Array.isArray(item.loc)
    ? item.loc.filter((part) => !["body", "query", "path"].includes(part)).join(" → ")
    : "";
  const message = text(item.msg || item.message || item.detail);
  return [location, message].filter(Boolean).join(": ");
}

function collectDetails(details) {
  if (Array.isArray(details)) return details.map(formatValidationItem).filter(Boolean);
  if (details && typeof details === "object") {
    if (Array.isArray(details.errors)) return collectDetails(details.errors);
    if (Array.isArray(details.validation_errors)) return collectDetails(details.validation_errors);
    return Object.entries(details)
      .map(([key, value]) => `${key.replaceAll("_", " ")}: ${typeof value === "string" ? value : JSON.stringify(value)}`)
      .filter(Boolean);
  }
  const message = text(details);
  return message ? [message] : [];
}

export function getApiErrorInfo(error) {
  const data = error?.details || error?.response?.data || error?.data || {};
  const payload = data?.error || data;
  const status = error?.status || error?.response?.status;
  const code = payload?.code || error?.code || "";
  const validation = collectDetails(payload?.details ?? data?.detail);
  const summary = text(payload?.message || data?.message || error?.message) || DEFAULT_MESSAGE;
  const isInternal = status >= 500 || code === "internal_server_error";
  const message = isInternal
    ? "The server could not complete this action. Please try again, and contact an administrator if it continues."
    : validation.length
      ? `${summary === "Request validation failed." ? "Please check the following fields" : summary}: ${validation.join("; ")}`
      : summary;

  return { title: isInternal ? "Server error" : status === 401 ? "Sign-in required" : status === 403 ? "Access denied" : status === 404 ? "Not found" : status === 409 ? "Conflict" : status === 422 ? "Check your input" : "Request failed", message, status, code, details: validation };
}

export function getErrorMessage(error, fallback = DEFAULT_MESSAGE) {
  const info = getApiErrorInfo(error);
  return info.message === DEFAULT_MESSAGE ? fallback : info.message;
}

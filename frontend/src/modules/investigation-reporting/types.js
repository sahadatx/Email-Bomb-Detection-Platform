export const EVIDENCE_TYPES = ["email_header", "content", "feature", "behavioral", "network", "other"];
export const EVIDENCE_STATUSES = ["pending", "verified", "flagged", "rejected"];
export const REPORT_TYPES = ["detection", "investigation", "campaign", "summary"];
export const REPORT_SECTIONS = [
  ["executive_summary", "Executive Summary"],
  ["detection_summary", "Detection Summary"],
  ["explainability", "Explainability"],
  ["evidence", "Evidence"],
  ["risk_analysis", "Risk Analysis"],
  ["behavioral_analysis", "Behavioral Analysis"],
  ["analyst_notes", "Analyst Notes"],
  ["technical_appendix", "Technical Appendix"],
];

export const REPORT_FORMATS = ["pdf", "json"];

export const EXPLANATION_STATUSES = ["available", "partial", "unavailable", "restricted"];

export const EMPTY_PAGE = { items: [], total: 0, page: 1, page_size: 30, total_pages: 1 };

export function investigationError(error, fallback = "Request could not be completed.") {
  const detail = error?.details?.detail;
  if (Array.isArray(detail)) return detail.map((item) => [item.loc?.slice(-1)[0], item.msg].filter(Boolean).join(": ")).join(" · ") || fallback;
  return detail?.message || detail || error?.message || fallback;
}

export const DEFAULT_FILTERS = Object.freeze({
  time_range: "24h",
  classification: "",
  risk_level: "",
  model_id: "",
  start_date: "",
  end_date: "",
});

export const TIME_RANGES = [
  ["24h", "Last 24 hours"],
  ["7d", "Last 7 days"],
  ["30d", "Last 30 days"],
  ["90d", "Last 90 days"],
  ["custom", "Custom range"],
];

export const CLASSIFICATIONS = [
  ["", "All classifications"],
  ["normal", "Normal"],
  ["bomb", "Bomb"],
];
export const RISK_LEVELS = [
  ["", "All risk levels"],
  ["critical", "Critical"],
  ["high", "High"],
  ["medium", "Medium"],
  ["low", "Low"],
];

export const QUICK_ACTIONS = [
  {
    label: "Review detections",
    description: "Search and investigate detection results",
    to: "/detection/history",
    icon: "scan",
  },
  {
    label: "Threat intelligence",
    description: "Review indicators, feeds and matches",
    to: "/threat-intelligence",
    icon: "shield",
  },
  {
    label: "Model registry",
    description: "Check active models and versions",
    to: "/ml-models/registry",
    icon: "cpu",
  },
  {
    label: "System administration",
    description: "Review jobs, settings and health",
    to: "/administration",
    icon: "settings",
  },
];

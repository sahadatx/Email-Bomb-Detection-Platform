export const SETTINGS_CATEGORIES = [
  { id: "general", label: "General", description: "Platform identity and timezone" },
  { id: "detection", label: "Detection", description: "Detection workflow options" },
  { id: "risk", label: "Risk", description: "Scoring thresholds" },
  { id: "models", label: "Models", description: "Default active model version" },
  { id: "email_processing", label: "Email Processing", description: "Ingestion and upload limits" },
  { id: "threat_intelligence", label: "Threat Intelligence", description: "Feed connectivity and ownership" },
  { id: "notifications", label: "Notifications", description: "Delivery provider status" },
  { id: "security", label: "Security", description: "Authentication policy" },
];

export const CATEGORY_ROUTE = (category) => `/settings/${category}`;

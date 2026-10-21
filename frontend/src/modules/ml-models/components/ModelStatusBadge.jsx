import React from "react";

const STATUS_CONFIG = {
  active: {
    label: "Active",
    className: "ml-status-badge--success",
  },
  inactive: {
    label: "Inactive",
    className: "ml-status-badge--neutral",
  },
  registered: {
    label: "Registered",
    className: "ml-status-badge--info",
  },
  archived: {
    label: "Archived",
    className: "ml-status-badge--neutral",
  },
  pending: {
    label: "Pending",
    className: "ml-status-badge--warning",
  },
  queued: {
    label: "Queued",
    className: "ml-status-badge--warning",
  },
  running: {
    label: "Running",
    className: "ml-status-badge--info",
  },
  completed: {
    label: "Completed",
    className: "ml-status-badge--success",
  },
  failed: {
    label: "Failed",
    className: "ml-status-badge--danger",
  },
  cancelled: {
    label: "Cancelled",
    className: "ml-status-badge--neutral",
  },
};

export default function ModelStatusBadge({ status }) {
  const normalizedStatus = String(status || "unknown").toLowerCase();

  const config = STATUS_CONFIG[normalizedStatus] || {
    label: normalizedStatus.replaceAll("_", " "),
    className: "ml-status-badge--neutral",
  };

  return (
    <span
      className={`ml-status-badge ${config.className}`}
      title={`Status: ${config.label}`}
    >
      <span className="ml-status-badge__dot" aria-hidden="true" />
      {config.label}
    </span>
  );
}
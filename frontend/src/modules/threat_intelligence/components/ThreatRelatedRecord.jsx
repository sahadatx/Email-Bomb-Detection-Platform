import { displayDate, displayLabel } from "../types/threatIntelligence";

const FIELD_LABELS = {
  id: "Record ID",
  email_id: "Email ID",
  source: "Source",
  source_identifier: "Source identifier",
  ground_truth_label: "Ground truth label",
  sender: "Sender",
  recipients: "Recipients",
  subject: "Subject",
  received_at: "Received at",
  collected_at: "Collected at",
  status: "Status",
  indicator_value: "Indicator",
  value: "Indicator",
  indicator_type: "Type",
  severity: "Severity",
  confidence: "Confidence",
  classification: "Classification",
  predicted_label: "Prediction",
  model_name: "Model",
  version: "Model version",
  created_at: "Created at",
  description: "Description",
  first_seen_at: "First seen",
  last_seen_at: "Last seen",
  expires_at: "Expires at",
  detection_id: "Detection ID",
};

const ALLOWED_FIELDS = {
  email: [
    "id",
    "source",
    "source_identifier",
    "ground_truth_label",
    "sender",
    "recipients",
    "subject",
    "received_at",
    "collected_at",
    "status",
  ],
  indicator: [
    "id",
    "value",
    "indicator_type",
    "severity",
    "confidence",
    "source",
    "status",
    "description",
    "first_seen_at",
    "last_seen_at",
    "expires_at",
  ],
  detection: [
    "id",
    "email_id",
    "predicted_label",
    "confidence",
    "status",
    "model_name",
    "version",
    "created_at",
  ],
};

function formatValue(key, value) {
  if (value === null || value === undefined || value === "") return "—";
  if (key.endsWith("_at")) return displayDate(value);
  if (key === "confidence" && typeof value === "number") {
    return `${(value <= 1 ? value * 100 : value).toFixed(1)}%`;
  }
  if (
    [
      "status",
      "source",
      "ground_truth_label",
      "indicator_type",
      "severity",
      "predicted_label",
    ].includes(key)
  ) {
    return displayLabel(String(value));
  }
  return String(value);
}

export default function ThreatRelatedRecord({ kind, data }) {
  if (!data || typeof data !== "object") {
    return <div className="ti-empty">The related record is unavailable.</div>;
  }

  const fields = ALLOWED_FIELDS[kind] || [];
  const title = displayLabel(kind || "related");

  return (
    <section className="ti-related-record" aria-label={`${title} details`}>
      <h3>{title} details</h3>
      <dl className="ti-definition-list">
        {fields
          .filter((key) => key in data)
          .map((key) => (
            <div className="ti-definition-row" key={key}>
              <dt>{FIELD_LABELS[key] || displayLabel(key)}</dt>
              <dd>{formatValue(key, data[key])}</dd>
            </div>
          ))}
      </dl>
      {kind === "detection" && data.risk && (
        <div className="ti-related-summary">
          <h4>Risk assessment</h4>
          <p>
            Score: {data.risk.score ?? "Unavailable"} · Level:{" "}
            {displayLabel(data.risk.level || "unavailable")}
          </p>
        </div>
      )}
      {kind === "detection" && data.behavioral && (
        <div className="ti-related-summary">
          <h4>Behavioral analysis</h4>
          <p>
            {data.behavioral.summary ||
              displayLabel(data.behavioral.status || "No summary available")}
          </p>
        </div>
      )}
      <p className="ti-muted">
        Sensitive message content and model feature snapshots are not shown in
        this drawer.
      </p>
    </section>
  );
}

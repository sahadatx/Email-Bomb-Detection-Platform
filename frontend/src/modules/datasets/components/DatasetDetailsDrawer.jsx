
import { useEffect, useMemo } from "react";
import {
  X,
  Mail,
  Database,
  Hash,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Copy,
} from "lucide-react";

const FEATURE_LABELS = [
  { key: "f1_sender_email", label: "F1", name: "Sender Email" },
  { key: "f2_known_domain", label: "F2", name: "Known Domain" },
  { key: "f3_message_id", label: "F3", name: "Message ID" },
  { key: "f4_auto_submitted", label: "F4", name: "Auto Submitted" },
  { key: "f5_precedence_bulk", label: "F5", name: "Precedence Bulk" },
  { key: "f6_list_id", label: "F6", name: "List ID" },
  { key: "f7_x_beenthere", label: "F7", name: "X-BeenThere" },
  { key: "f8_x_anti_abuse", label: "F8", name: "X-Anti-Abuse" },
  { key: "f9_keyword_features", label: "F9", name: "Keyword Features" },
  { key: "f10_subject_length", label: "F10", name: "Subject Length" },
  { key: "f11_emails_per_minute", label: "F11", name: "Emails Per Minute" },
  { key: "f12_emails_per_hour", label: "F12", name: "Emails Per Hour" },
];

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function firstDefined(...values) {
  return values.find((value) => value !== undefined && value !== null);
}

function firstNonEmpty(...values) {
  return values.find(
    (value) =>
      value !== undefined &&
      value !== null &&
      String(value).trim() !== ""
  );
}

function unwrapEmail(value) {
  let current = value;

  for (let index = 0; index < 5; index += 1) {
    if (!isObject(current)) {
      return null;
    }

    if (isObject(current.email)) {
      current = current.email;
      continue;
    }

    if (isObject(current.data)) {
      current = current.data;
      continue;
    }

    break;
  }

  return isObject(current) ? current : null;
}

function formatValue(value) {
  if (value === undefined || value === null || value === "") {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }

  return String(value);
}

function formatDate(value) {
  if (value === undefined || value === null || value === "") {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(date);
}

function normalizeGroundTruth(value) {
  const normalized = String(value ?? "").trim().toLowerCase();

  if (["normal", "ham", "0"].includes(normalized)) {
    return "Normal";
  }

  if (
    ["bomb", "bombing", "email_bomb", "email-bomb", "1"].includes(
      normalized
    )
  ) {
    return "Bombing";
  }

  return value ? String(value) : "Unknown";
}

function getGroundTruthClass(value) {
  const normalized = normalizeGroundTruth(value).toLowerCase();

  if (normalized === "normal") {
    return "dataset-label--normal";
  }

  if (normalized === "bombing") {
    return "dataset-label--bombing";
  }

  return "dataset-label--unknown";
}

function getIdentity(email) {
  return isObject(email?.identity) ? email.identity : {};
}

function getTimeInformation(email) {
  return isObject(email?.time) ? email.time : {};
}

function getFeatureValues(email) {
  return isObject(email?.feature_vector) ? email.feature_vector : {};
}

function getFeatureSchema(email) {
  return isObject(email?.feature_schema) ? email.feature_schema : {};
}

function getEmailIdentity(email) {
  const identity = getIdentity(email);

  return {
    subject: firstNonEmpty(identity.subject, email?.subject),
    sender: firstNonEmpty(
      identity.sender,
      identity.sender_email,
      email?.sender,
      email?.sender_email
    ),
    messageId: firstNonEmpty(
      identity.message_id,
      identity.messageId,
      email?.message_id,
      email?.messageId
    ),
    emailId: firstNonEmpty(
      identity.email_id,
      identity.id,
      email?.email_id,
      email?.id,
      email?.sample_id
    ),
    groundTruth: firstDefined(
      identity.ground_truth,
      identity.label,
      email?.ground_truth,
      email?.label
    ),
  };
}

function getSourceInformation(email) {
  const identity = getIdentity(email);
  const time = getTimeInformation(email);

  return {
    source: firstNonEmpty(
      identity.source,
      identity.source_type,
      email?.source,
      email?.source_type
    ),
    sourceIdentifier: firstNonEmpty(
      identity.source_identifier,
      identity.source_id,
      email?.source_identifier,
      email?.source_id
    ),
    receivedAt: firstDefined(time.received_at, email?.received_at),
    collectedAt: firstDefined(time.collected_at, email?.collected_at),
    parsedAt: firstDefined(time.parsed_at, email?.parsed_at),
    extractedAt: firstDefined(time.extracted_at, email?.extracted_at),
  };
}

function getFeatureDescription(schema, key) {
  const definition = schema?.[key];

  if (typeof definition === "string") {
    return definition;
  }

  if (!isObject(definition)) {
    return null;
  }

  return firstNonEmpty(
    definition.description,
    definition.label,
    definition.name
  );
}

function DetailField({ label, value, code = false }) {
  return (
    <div className="dataset-details-field">
      <span>{label}</span>
      {code ? (
        <code>{formatValue(value)}</code>
      ) : (
        <strong>{formatValue(value)}</strong>
      )}
    </div>
  );
}

function FeatureRow({ feature, value, description }) {
  return (
    <div
      className="dataset-feature-row"
      title={description || feature.name}
    >
      <div className="dataset-feature-row__identity">
        <span className="dataset-feature-row__code">
          {feature.label}
        </span>
        <span className="dataset-feature-row__name">
          {feature.name}
        </span>
      </div>

      <code className="dataset-feature-row__value">
        {formatValue(value)}
      </code>
    </div>
  );
}

export default function DatasetDetailsDrawer({
  open = false,
  email = null,
  loading = false,
  error = null,
  onClose,
  className = "",
}) {
  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  const normalizedEmail = useMemo(() => unwrapEmail(email), [email]);

  const identity = useMemo(
    () => getEmailIdentity(normalizedEmail),
    [normalizedEmail]
  );

  const sourceInfo = useMemo(
    () => getSourceInformation(normalizedEmail),
    [normalizedEmail]
  );

  const features = useMemo(
    () => getFeatureValues(normalizedEmail),
    [normalizedEmail]
  );

  const featureSchema = useMemo(
    () => getFeatureSchema(normalizedEmail),
    [normalizedEmail]
  );

  const metadata = useMemo(() => {
    if (!normalizedEmail) {
      return null;
    }

    return firstDefined(
      normalizedEmail.metadata,
      normalizedEmail.email_metadata,
      normalizedEmail.headers_metadata
    );
  }, [normalizedEmail]);

  const handleCopy = async (value) => {
    if (!value || !navigator?.clipboard?.writeText) {
      return;
    }

    try {
      await navigator.clipboard.writeText(String(value));
    } catch {
      // Clipboard access may be unavailable in insecure contexts.
    }
  };

  if (!open) {
    return null;
  }

  return (
    <div
      className="dataset-drawer-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose?.();
        }
      }}
    >
      <aside
        className={`dataset-details-drawer ${className}`.trim()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dataset-details-title"
      >
        <header className="dataset-details-drawer__header">
          <div>
            <span className="dataset-details-drawer__eyebrow">
              Dataset Workspace
            </span>
            <h2 id="dataset-details-title">Email Details</h2>
          </div>

          <button
            type="button"
            className="dataset-icon-button"
            onClick={onClose}
            aria-label="Close email details"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </header>

        {loading ? (
          <div className="dataset-details-drawer__state" role="status">
            <span className="dataset-spinner" />
            <p>Loading email details...</p>
          </div>
        ) : error ? (
          <div
            className="dataset-details-drawer__state dataset-details-drawer__state--error"
            role="alert"
          >
            <AlertTriangle size={22} aria-hidden="true" />
            <p>{error}</p>
          </div>
        ) : !normalizedEmail ? (
          <div className="dataset-details-drawer__state">
            <Mail size={28} aria-hidden="true" />
            <p>No email selected.</p>
          </div>
        ) : (
          <div className="dataset-details-drawer__body">
            <section className="dataset-details-card">
              <div className="dataset-details-card__title">
                <Mail size={17} aria-hidden="true" />
                <h3>Email Identity</h3>
              </div>

              <DetailField
                label="Subject"
                value={identity.subject || "(No subject)"}
              />
              <DetailField label="Sender" value={identity.sender} />
              <DetailField
                label="Message ID"
                value={identity.messageId}
                code
              />
              <DetailField
                label="Email ID"
                value={identity.emailId}
                code
              />

              <div className="dataset-details-field">
                <span>Ground Truth</span>
                <strong>
                  <span
                    className={`dataset-label ${getGroundTruthClass(
                      identity.groundTruth
                    )}`}
                  >
                    {normalizeGroundTruth(identity.groundTruth)}
                  </span>
                </strong>
              </div>

              {identity.emailId && (
                <button
                  type="button"
                  className="dataset-button dataset-button--ghost"
                  onClick={() => handleCopy(identity.emailId)}
                >
                  <Copy size={15} aria-hidden="true" />
                  Copy Email ID
                </button>
              )}
            </section>

            <section className="dataset-details-card">
              <div className="dataset-details-card__title">
                <Database size={17} aria-hidden="true" />
                <h3>Source Information</h3>
              </div>

              <DetailField label="Source" value={sourceInfo.source} />
              <DetailField
                label="Source Identifier"
                value={sourceInfo.sourceIdentifier}
                code
              />
              <DetailField
                label="Received"
                value={formatDate(sourceInfo.receivedAt)}
              />
              <DetailField
                label="Collected At"
                value={formatDate(sourceInfo.collectedAt)}
              />
              <DetailField
                label="Parsed At"
                value={formatDate(sourceInfo.parsedAt)}
              />
              <DetailField
                label="Extracted At"
                value={formatDate(sourceInfo.extractedAt)}
              />
            </section>

            <section className="dataset-details-card">
              <div className="dataset-details-card__title">
                <ShieldCheck size={17} aria-hidden="true" />
                <div>
                  <h3>Canonical Features</h3>
                  <p>F1–F12 values provided by Module 04</p>
                </div>
              </div>

              <div className="dataset-feature-list">
                {FEATURE_LABELS.map((feature) => (
                  <FeatureRow
                    key={feature.key}
                    feature={feature}
                    value={features[feature.key]}
                    description={getFeatureDescription(
                      featureSchema,
                      feature.key
                    )}
                  />
                ))}
              </div>
            </section>

            {isObject(metadata) && Object.keys(metadata).length > 0 && (
              <section className="dataset-details-card">
                <div className="dataset-details-card__title">
                  <Hash size={17} aria-hidden="true" />
                  <h3>Metadata</h3>
                </div>

                <pre className="dataset-details-json">
                  {JSON.stringify(metadata, null, 2)}
                </pre>
              </section>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
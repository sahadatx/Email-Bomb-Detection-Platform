import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react";

const SEVERITY_CONFIG = {
  error: {
    label: "Error",
    className: "is-error",
    icon: AlertCircle,
  },
  critical: {
    label: "Critical",
    className: "is-error",
    icon: AlertCircle,
  },
  high: {
    label: "High",
    className: "is-error",
    icon: AlertCircle,
  },
  warning: {
    label: "Warning",
    className: "is-warning",
    icon: AlertTriangle,
  },
  medium: {
    label: "Medium",
    className: "is-warning",
    icon: AlertTriangle,
  },
  info: {
    label: "Info",
    className: "is-info",
    icon: Info,
  },
  low: {
    label: "Low",
    className: "is-info",
    icon: Info,
  },
};

function normalizeSeverity(severity) {
  const value = String(severity ?? "info")
    .trim()
    .toLowerCase();

  return SEVERITY_CONFIG[value] ? value : "info";
}

function getIssueTitle(issue) {
  return (
    issue?.title ??
    issue?.name ??
    issue?.check_name ??
    issue?.check ??
    issue?.code ??
    "Validation issue"
  );
}

function getIssueMessage(issue) {
  return (
    issue?.message ??
    issue?.description ??
    issue?.detail ??
    issue?.details ??
    "No additional details provided."
  );
}

function getIssueId(issue, index) {
  return (
    issue?.issue_id ??
    issue?.id ??
    issue?.check_id ??
    `${issue?.check ?? issue?.check_name ?? "issue"}-${index}`
  );
}

function getSampleId(issue) {
  return (
    issue?.email_id ??
    issue?.sample_id ??
    issue?.record_id ??
    issue?.row_id ??
    null
  );
}

function getField(issue) {
  return (
    issue?.field ??
    issue?.feature ??
    issue?.column ??
    issue?.feature_name ??
    null
  );
}

function getRecommendation(issue) {
  return (
    issue?.recommendation ??
    issue?.suggestion ??
    issue?.remediation ??
    null
  );
}

function getCheckName(issue) {
  return issue?.check_name ?? issue?.check ?? null;
}

function getIssueList(issues) {
  if (Array.isArray(issues)) {
    return issues;
  }

  if (Array.isArray(issues?.items)) {
    return issues.items;
  }

  if (Array.isArray(issues?.issues)) {
    return issues.issues;
  }

  if (Array.isArray(issues?.findings)) {
    return issues.findings;
  }

  return [];
}

function formatValue(value) {
  if (typeof value === "string") {
    return value;
  }

  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  return String(value);
}

function IssueMetadata({ issue }) {
  const sampleId = getSampleId(issue);
  const field = getField(issue);

  if (!sampleId && !field) {
    return null;
  }

  return (
    <div className="dataset-validation-issue__metadata">
      {sampleId && (
        <span>
          Sample:{" "}
          <code>{formatValue(sampleId)}</code>
        </span>
      )}

      {field && (
        <span>
          Field:{" "}
          <code>{formatValue(field)}</code>
        </span>
      )}
    </div>
  );
}

function IssueRecommendation({ issue }) {
  const recommendation = getRecommendation(issue);

  if (!recommendation) {
    return null;
  }

  return (
    <div className="dataset-validation-issue__recommendation">
      <strong>Recommendation:</strong>{" "}
      <span>{formatValue(recommendation)}</span>
    </div>
  );
}

function ValidationIssue({ issue, index }) {
  const severity = normalizeSeverity(
    issue?.severity ?? issue?.level ?? issue?.status
  );

  const config = SEVERITY_CONFIG[severity];
  const Icon = config.icon;
  const title = getIssueTitle(issue);
  const message = getIssueMessage(issue);
  const checkName = getCheckName(issue);

  return (
    <article
      className="dataset-validation-issue"
      key={getIssueId(issue, index)}
    >
      <div
        className={`dataset-validation-issue__severity ${config.className}`}
        aria-label={`Severity: ${config.label}`}
      >
        <Icon size={17} aria-hidden="true" />
        <span>{config.label}</span>
      </div>

      <div className="dataset-validation-issue__body">
        <div className="dataset-validation-issue__title-row">
          <h3>{formatValue(title)}</h3>

          {checkName && (
            <span className="dataset-validation-issue__check">
              {formatValue(checkName)}
            </span>
          )}
        </div>

        <p>{formatValue(message)}</p>

        <IssueMetadata issue={issue} />

        <IssueRecommendation issue={issue} />
      </div>
    </article>
  );
}

function LoadingState() {
  return (
    <div
      className="dataset-validation-issues__empty"
      role="status"
      aria-live="polite"
    >
      <span
        className="dataset-loading-spinner"
        aria-hidden="true"
      />
      <p>Loading validation issues...</p>
    </div>
  );
}

function EmptyState({ message }) {
  return (
    <div className="dataset-validation-issues__empty">
      <CheckCircle2 size={26} aria-hidden="true" />
      <strong>No issues found</strong>
      <p>{message}</p>
    </div>
  );
}

export default function DatasetValidationIssues({
  issues = [],
  loading = false,
  emptyMessage = "No validation issues were reported for this validation run.",
  className = "",
}) {
  const normalizedIssues = getIssueList(issues);

  return (
    <section
      className={`dataset-validation-issues ${className}`.trim()}
      aria-label="Validation issues"
      aria-busy={loading}
    >
      <div className="dataset-validation-issues__header">
        <div>
          <h2>Validation Issues</h2>
          <p>
            Review errors, warnings, and other validation findings.
          </p>
        </div>

        <span className="dataset-validation-issues__count">
          {loading
            ? "Loading..."
            : `${normalizedIssues.length.toLocaleString()} ${
                normalizedIssues.length === 1 ? "issue" : "issues"
              }`}
        </span>
      </div>

      {loading ? (
        <LoadingState />
      ) : normalizedIssues.length === 0 ? (
        <EmptyState message={emptyMessage} />
      ) : (
        <div className="dataset-validation-issues__list">
          {normalizedIssues.map((issue, index) => (
            <ValidationIssue
              key={getIssueId(issue, index)}
              issue={issue}
              index={index}
            />
          ))}
        </div>
      )}
    </section>
  );
}
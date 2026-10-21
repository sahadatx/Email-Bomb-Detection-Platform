import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock3,
  ShieldCheck,
  ListChecks,
} from "lucide-react";

const STATUS_CONFIG = {
  passed: {
    label: "Passed",
    className: "is-passed",
    icon: CheckCircle2,
  },
  failed: {
    label: "Failed",
    className: "is-failed",
    icon: XCircle,
  },
  warning: {
    label: "Warnings",
    className: "is-warning",
    icon: AlertTriangle,
  },
  pending: {
    label: "Pending",
    className: "is-pending",
    icon: Clock3,
  },
};

const STAT_CARDS = [
  {
    key: "checks",
    label: "Total Checks",
    icon: ListChecks,
    className: "dataset-validation-stat--total",
  },
  {
    key: "passed",
    label: "Passed",
    icon: CheckCircle2,
    className: "dataset-validation-stat--passed",
  },
  {
    key: "failed",
    label: "Failed",
    icon: XCircle,
    className: "dataset-validation-stat--failed",
  },
  {
    key: "warnings",
    label: "Warnings",
    icon: AlertTriangle,
    className: "dataset-validation-stat--warning",
  },
];

function normalizeStatus(status) {
  const value = String(status ?? "")
    .trim()
    .toLowerCase();

  if (["passed", "pass", "success", "valid"].includes(value)) {
    return "passed";
  }

  if (["failed", "fail", "error", "invalid"].includes(value)) {
    return "failed";
  }

  if (["warning", "warnings", "partial"].includes(value)) {
    return "warning";
  }

  return "pending";
}

function getNumber(value, fallback = 0) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  const number = Number(value);

  return Number.isFinite(number) && number >= 0
    ? number
    : fallback;
}

function getFirstNumber(...values) {
  for (const value of values) {
    if (value !== null && value !== undefined && value !== "") {
      return getNumber(value);
    }
  }

  return 0;
}

function formatNumber(value) {
  return getNumber(value).toLocaleString();
}

function formatDate(value) {
  if (!value) {
    return null;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toLocaleString();
}

function getValidationMessage(status, result) {
  const message =
    result.message ??
    result.summary_message ??
    result.detail;

  if (typeof message === "string" && message.trim()) {
    return message;
  }

  switch (status) {
    case "passed":
      return "All reported validation checks passed.";

    case "failed":
      return "One or more validation checks failed.";

    case "warning":
      return "Validation completed with warnings.";

    default:
      return "Run validation to inspect this dataset.";
  }
}

function getSummary(validation) {
  if (!validation || typeof validation !== "object") {
    return {};
  }

  if (
    validation.summary &&
    typeof validation.summary === "object"
  ) {
    return validation.summary;
  }

  return validation;
}

export default function DatasetValidationSummary({
  validation,
  loading = false,
  className = "",
}) {
  const result = getSummary(validation);

  const hasResult =
    validation !== null &&
    validation !== undefined &&
    Object.keys(result).length > 0;

  const status = hasResult
    ? normalizeStatus(
        result.status ??
          result.validation_status ??
          result.overall_status
      )
    : "pending";

  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  const checks = getFirstNumber(
    result.total_checks,
    result.checks_total,
    result.check_count,
    result.total
  );

  const passed = getFirstNumber(
    result.passed_checks,
    result.checks_passed,
    result.passed
  );

  const failed = getFirstNumber(
    result.failed_checks,
    result.checks_failed,
    result.failed
  );

  const warnings = getFirstNumber(
    result.warning_checks,
    result.checks_warning,
    result.warnings
  );

  const issues = getFirstNumber(
    result.total_issues,
    result.issue_count,
    Array.isArray(validation?.issues)
      ? validation.issues.length
      : undefined
  );

  const validatedAt =
    formatDate(result.validated_at) ??
    formatDate(result.created_at);

  const message = getValidationMessage(status, result);

  const cards = STAT_CARDS.map((card) => {
    const values = {
      checks,
      passed,
      failed,
      warnings,
    };

    return {
      ...card,
      value: values[card.key],
    };
  });

  return (
    <section
      className={`dataset-validation-summary ${className}`.trim()}
      aria-label="Dataset validation summary"
      aria-busy={loading}
    >
      <div className="dataset-validation-summary__header">
        <div>
          <h2>Validation Summary</h2>
          <p>
            Overview of the latest dataset validation result.
          </p>
        </div>

        <div
          className={`dataset-validation-status ${statusConfig.className}`}
          role="status"
          aria-live="polite"
        >
          <StatusIcon size={17} aria-hidden="true" />
          <span>
            {loading ? "Loading" : statusConfig.label}
          </span>
        </div>
      </div>

      <div className="dataset-validation-summary__status-card">
        <div className="dataset-validation-summary__status-icon">
          <ShieldCheck size={22} aria-hidden="true" />
        </div>

        <div className="dataset-validation-summary__status-content">
          <span className="dataset-validation-summary__eyebrow">
            Overall Status
          </span>

          <strong>
            {loading
              ? "Loading validation..."
              : hasResult
                ? statusConfig.label
                : "Not Run"}
          </strong>

          <span>
            {loading
              ? "Retrieving validation results."
              : message}
          </span>
        </div>
      </div>

      <div className="dataset-validation-summary__cards">
        {cards.map((card) => {
          const Icon = card.icon;

          return (
            <article
              key={card.key}
              className={`dataset-validation-stat ${card.className}`}
            >
              <div className="dataset-validation-stat__icon">
                <Icon size={19} aria-hidden="true" />
              </div>

              <div className="dataset-validation-stat__content">
                <span>{card.label}</span>

                <strong>
                  {loading || !hasResult
                    ? "—"
                    : formatNumber(card.value)}
                </strong>
              </div>
            </article>
          );
        })}
      </div>

      <div className="dataset-validation-summary__footer">
        <span>
          Total Issues:{" "}
          <strong>
            {loading || !hasResult
              ? "—"
              : formatNumber(issues)}
          </strong>
        </span>

        <span>
          Last validated:{" "}
          <strong>
            {loading || !hasResult
              ? "—"
              : validatedAt ?? "—"}
          </strong>
        </span>
      </div>
    </section>
  );
}
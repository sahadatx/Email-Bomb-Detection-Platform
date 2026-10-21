import {
  CheckCircle2,
  Database,
  Info,
  Layers3,
  Lock,
} from "lucide-react";

// ============================================================================
// CONSTANTS
// ============================================================================

const SPLITS = [
  {
    key: "train",
    label: "Training",
    percentageKeys: [
      "training_percentage",
      "train_percentage",
      "train_percent",
      "train_split_percentage",
    ],
    countKeys: [
      "train_count",
      "training_count",
      "train_sample_count",
      "training_sample_count",
    ],
    color: "blue",
  },
  {
    key: "validation",
    label: "Validation",
    percentageKeys: [
      "validation_percentage",
      "validation_percent",
      "validation_split_percentage",
    ],
    countKeys: [
      "validation_count",
      "validation_sample_count",
    ],
    color: "violet",
  },
  {
    key: "test",
    label: "Test",
    percentageKeys: [
      "testing_percentage",
      "test_percentage",
      "test_percent",
      "test_split_percentage",
    ],
    countKeys: [
      "test_count",
      "testing_count",
      "test_sample_count",
      "testing_sample_count",
    ],
    color: "green",
  },
];

// ============================================================================
// DATA HELPERS
// ============================================================================

function getVersion(selection) {
  return (
    selection?.dataset_version ??
    selection?.version ??
    selection ??
    null
  );
}

function getFirstDefined(source, keys) {
  for (const key of keys) {
    const value = source?.[key];

    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }

  return null;
}

function getSplitContainer(selection, version) {
  return (
    selection?.split ??
    selection?.splits ??
    selection?.split_configuration ??
    version?.split ??
    version?.splits ??
    version?.split_configuration ??
    null
  );
}

function getSplitPercentage(selection, version, split) {
  const container = getSplitContainer(selection, version);

  const directValue = getFirstDefined(version, split.percentageKeys);

  if (directValue !== null) {
    return directValue;
  }

  const nestedValue = getFirstDefined(
    container,
    split.percentageKeys,
  );

  if (nestedValue !== null) {
    return nestedValue;
  }

  const splitValue =
    container?.[split.key] ??
    selection?.[split.key] ??
    version?.[split.key];

  if (splitValue && typeof splitValue === "object") {
    return (
      splitValue.percentage ??
      splitValue.percent ??
      splitValue.split_percentage ??
      null
    );
  }

  return null;
}

function getSplitCount(selection, version, split) {
  const directCount = getFirstDefined(version, split.countKeys);

  if (directCount !== null) {
    return directCount;
  }

  const container = getSplitContainer(selection, version);

  const nestedCount = getFirstDefined(container, split.countKeys);

  if (nestedCount !== null) {
    return nestedCount;
  }

  const splitCounts =
    selection?.split_counts ??
    selection?.split_counts_by_name ??
    version?.split_counts ??
    version?.split_counts_by_name ??
    container?.split_counts ??
    null;

  if (splitCounts && typeof splitCounts === "object") {
    const value = splitCounts[split.key];

    if (value !== undefined && value !== null) {
      if (typeof value === "object") {
        return (
          value.count ??
          value.sample_count ??
          value.samples ??
          null
        );
      }

      return value;
    }
  }

  const splitValue =
    container?.[split.key] ??
    selection?.[split.key] ??
    version?.[split.key];

  if (splitValue && typeof splitValue === "object") {
    return (
      splitValue.count ??
      splitValue.sample_count ??
      splitValue.samples ??
      null
    );
  }

  return null;
}

function getDatasetName(selection, version) {
  return (
    selection?.dataset?.name ??
    version?.dataset?.name ??
    version?.dataset_name ??
    selection?.dataset_name ??
    version?.name ??
    "Dataset"
  );
}

function getVersionLabel(version) {
  if (
    version?.version_number !== null &&
    version?.version_number !== undefined
  ) {
    return `v${version.version_number}`;
  }

  if (version?.version !== null && version?.version !== undefined) {
    if (typeof version.version === "number") {
      return `v${version.version}`;
    }

    return String(version.version);
  }

  if (version?.name) {
    return String(version.name);
  }

  return "—";
}

function getTotalSamples(selection, version) {
  return (
    version?.sample_count ??
    version?.total_samples ??
    version?.total_count ??
    selection?.sample_count ??
    selection?.total_samples ??
    selection?.total_count ??
    null
  );
}

// ============================================================================
// FORMAT HELPERS
// ============================================================================

function formatPercentage(value) {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "Not available";
  }

  return `${number}%`;
}

function formatCount(value) {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "Not available";
  }

  return number.toLocaleString();
}

function getProgressWidth(value) {
  if (value === null || value === undefined || value === "") {
    return 0;
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, Math.min(100, number));
}

// ============================================================================
// SPLIT CARD
// ============================================================================

function SplitCard({ split, percentage, count }) {
  const hasPercentage =
    percentage !== null &&
    percentage !== undefined &&
    percentage !== "" &&
    Number.isFinite(Number(percentage));

  const progressWidth = getProgressWidth(percentage);

  return (
    <article
      className={`preprocessing-split-card preprocessing-split-${split.color}`}
    >
      <div className="preprocessing-split-card-heading">
        <span>{split.label}</span>

        {hasPercentage && (
          <CheckCircle2 size={17} aria-hidden="true" />
        )}
      </div>

      <strong className="preprocessing-split-percentage">
        {formatPercentage(percentage)}
      </strong>

      <span className="preprocessing-split-count">
        {formatCount(count)} samples
      </span>

      {hasPercentage && (
        <div
          className="preprocessing-split-progress"
          role="progressbar"
          aria-label={`${split.label} split`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progressWidth}
        >
          <div
            className="preprocessing-split-progress-value"
            style={{ width: `${progressWidth}%` }}
          />
        </div>
      )}
    </article>
  );
}

// ============================================================================
// EMPTY STATE
// ============================================================================

function EmptySplitInformation() {
  return (
    <div className="preprocessing-empty-state">
      <Database size={22} aria-hidden="true" />

      <p>
        Select a validated dataset version to view its split
        information.
      </p>
    </div>
  );
}

// ============================================================================
// SPLIT INFORMATION
// ============================================================================

export default function SplitInformation({ selection = null }) {
  const version = getVersion(selection);

  const hasSelection = Boolean(
    version &&
      typeof version === "object" &&
      (version.id || version.version_id || version.dataset_version_id),
  );

  const totalSamples = hasSelection
    ? getTotalSamples(selection, version)
    : null;

  return (
    <section
      className="preprocessing-panel preprocessing-split-information"
      aria-labelledby="preprocessing-split-title"
    >
      <div className="preprocessing-panel-heading">
        <div className="preprocessing-heading-icon">
          <Layers3 size={19} aria-hidden="true" />
        </div>

        <div className="preprocessing-heading-copy">
          <h2 id="preprocessing-split-title">
            Dataset Split Information
          </h2>

          <p>
            Read-only split configuration from the selected dataset
            version.
          </p>
        </div>

        <span className="preprocessing-readonly-badge">
          <Lock size={13} aria-hidden="true" />
          Read only
        </span>
      </div>

      {!hasSelection ? (
        <EmptySplitInformation />
      ) : (
        <>
          <div className="preprocessing-split-dataset">
            <div>
              <span className="preprocessing-result-eyebrow">
                Selected dataset version
              </span>

              <strong>{getDatasetName(selection, version)}</strong>
            </div>

            <span className="preprocessing-split-version">
              Version {getVersionLabel(version)}
            </span>
          </div>

          <div className="preprocessing-split-grid">
            {SPLITS.map((split) => {
              const percentage = getSplitPercentage(
                selection,
                version,
                split,
              );

              const count = getSplitCount(
                selection,
                version,
                split,
              );

              return (
                <SplitCard
                  key={split.key}
                  split={split}
                  percentage={percentage}
                  count={count}
                />
              );
            })}
          </div>

          <div className="preprocessing-split-total">
            <span>Total dataset samples</span>
            <strong>{formatCount(totalSamples)}</strong>
          </div>

          <div className="preprocessing-info-notice">
            <Info size={16} aria-hidden="true" />

            <span>
              Split values are read-only. The preprocessing pipeline
              must use the split assignments stored in the selected
              dataset version. Values unavailable from the API are
              displayed as Not available.
            </span>
          </div>
        </>
      )}
    </section>
  );
}

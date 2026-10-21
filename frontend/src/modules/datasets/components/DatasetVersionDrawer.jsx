import { useEffect, useMemo } from "react";

import {
  X,
  GitBranch,
  Shuffle,
  Layers,
  ShieldCheck,
  FileText,
  AlertCircle,
  Database,
  Calendar,
} from "lucide-react";

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

const SPLITS = [
  {
    key: "training",
    label: "Training",
    color: "train",
    percentageKey: "training_percentage",
  },
  {
    key: "validation",
    label: "Validation",
    color: "validation",
    percentageKey: "validation_percentage",
  },
  {
    key: "testing",
    label: "Testing",
    color: "test",
    percentageKey: "testing_percentage",
  },
];

/* -------------------------------------------------------------------------- */
/* Value Helpers                                                              */
/* -------------------------------------------------------------------------- */

function getVersionId(version) {
  return version?.id ?? version?.version_id ?? "—";
}

function getVersionNumber(version) {
  const number = Number(version?.version_number);

  return Number.isInteger(number) && number > 0
    ? number
    : null;
}

function getVersionName(version) {
  return (
    version?.name ??
    version?.version_name ??
    "Unnamed Version"
  );
}

function getDatasetId(version) {
  return (
    version?.dataset_id ??
    version?.dataset?.id ??
    version?.dataset?.dataset_id ??
    null
  );
}

function getDatasetName(version, datasets = []) {
  const directName =
    version?.dataset_name ??
    version?.dataset?.name ??
    version?.dataset?.dataset_name;

  if (directName) {
    return directName;
  }

  const datasetId = getDatasetId(version);

  if (!datasetId) {
    return "—";
  }

  const dataset = datasets.find((item) => {
    const id = item?.id ?? item?.dataset_id;

    return (
      id != null &&
      String(id) === String(datasetId)
    );
  });

  return (
    dataset?.name ??
    dataset?.dataset_name ??
    "Unknown Dataset"
  );
}

function formatStatus(status) {
  if (!status) {
    return "Unknown";
  }

  return String(status)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatNumber(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toLocaleString()
    : "—";
}

function formatValue(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

/* -------------------------------------------------------------------------- */
/* Split Helpers                                                              */
/* -------------------------------------------------------------------------- */

function getSplitConfiguration(version) {
  return version?.split ?? {};
}

function getSplitPercentage(version, key) {
  const value = getSplitConfiguration(version)?.[key];

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) && number >= 0
    ? number
    : null;
}

function getSplitCount(version, key) {
  const value = version?.split_counts?.[key];

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  const count = Number(value);

  return Number.isFinite(count) && count >= 0
    ? count
    : null;
}

function getTotalSamples(version) {
  const value = version?.sample_count;

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  const count = Number(value);

  return Number.isFinite(count) && count >= 0
    ? count
    : null;
}

/* -------------------------------------------------------------------------- */
/* Feature Schema Helpers                                                     */
/* -------------------------------------------------------------------------- */

function getFeatureSchema(version) {
  return version?.feature_schema ?? null;
}

function getFeatures(schema) {
  if (Array.isArray(schema)) {
    return schema;
  }

  if (Array.isArray(schema?.features)) {
    return schema.features;
  }

  return [];
}

function getFeatureName(feature, index) {
  if (typeof feature === "string") {
    return feature;
  }

  return (
    feature?.name ??
    feature?.label ??
    feature?.key ??
    feature?.code ??
    `Feature ${index + 1}`
  );
}

function getFeatureKey(feature) {
  if (typeof feature === "string") {
    return feature;
  }

  return (
    feature?.key ??
    feature?.code ??
    feature?.name ??
    null
  );
}

function getFeatureDescription(feature) {
  if (typeof feature !== "object" || feature === null) {
    return null;
  }

  return (
    feature?.description ??
    feature?.definition ??
    feature?.type ??
    null
  );
}

/* -------------------------------------------------------------------------- */
/* Validation Helpers                                                         */
/* -------------------------------------------------------------------------- */

function getValidationSummary(version) {
  return version?.validation_summary ?? null;
}

function getValidationStatus(version) {
  if (version?.validation_passed === true) {
    return "passed";
  }

  if (version?.validation_passed === false) {
    return "failed";
  }

  const summary = getValidationSummary(version);

  if (typeof summary === "object" && summary !== null) {
    return (
      summary.status ??
      "not_validated"
    );
  }

  return "not_validated";
}

function getValidationMessage(version) {
  const summary = getValidationSummary(version);

  if (typeof summary === "string") {
    return summary;
  }

  if (summary && typeof summary === "object") {
    return (
      summary.message ??
      summary.detail ??
      summary.status ??
      null
    );
  }

  return null;
}

function getValidationDetails(version) {
  const summary = getValidationSummary(version);

  if (!summary || typeof summary !== "object") {
    return [];
  }

  return Object.entries(summary).filter(
    ([key, value]) =>
      key !== "status" &&
      key !== "message" &&
      key !== "detail" &&
      value !== null &&
      value !== undefined
  );
}

/* -------------------------------------------------------------------------- */
/* Error Helpers                                                              */
/* -------------------------------------------------------------------------- */

function getErrorMessage(error) {
  if (typeof error === "string") {
    return error;
  }

  if (Array.isArray(error)) {
    return error
      .map((item) => item?.msg ?? String(item))
      .join("; ");
  }

  return (
    error?.response?.data?.detail ??
    error?.response?.data?.message ??
    error?.response?.data?.error?.message ??
    error?.message ??
    "Unable to load version details."
  );
}

/* -------------------------------------------------------------------------- */
/* Reusable UI Components                                                     */
/* -------------------------------------------------------------------------- */

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

function SectionTitle({
  icon: Icon,
  title,
  description,
}) {
  return (
    <div className="dataset-details-card__title">
      <Icon size={17} />

      <div>
        <h3>{title}</h3>

        {description && <p>{description}</p>}
      </div>
    </div>
  );
}

function EmptyState({ children }) {
  return (
    <p className="dataset-details-schema-empty">
      {children}
    </p>
  );
}

/* -------------------------------------------------------------------------- */
/* Version Information                                                        */
/* -------------------------------------------------------------------------- */

function VersionInformation({ version, datasets }) {
  const versionNumber = getVersionNumber(version);
  const datasetName = getDatasetName(version, datasets);

  return (
    <section className="dataset-details-card">
      <SectionTitle
        icon={GitBranch}
        title="Version Information"
        description="Identity and summary of this dataset version."
      />

      {versionNumber !== null && (
        <DetailField
          label="Version Number"
          value={`v${versionNumber}`}
        />
      )}

      <DetailField
        label="Version Name"
        value={getVersionName(version)}
      />

      <DetailField
        label="Version ID"
        value={getVersionId(version)}
        code
      />

      <DetailField
        label="Dataset Name"
        value={datasetName}
      />

      <DetailField
        label="Dataset ID"
        value={getDatasetId(version)}
        code
      />

      <DetailField
        label="Status"
        value={formatStatus(version.status)}
      />

      <DetailField
        label="Total Samples"
        value={formatNumber(getTotalSamples(version))}
      />

      <DetailField
        label="Normal Samples"
        value={formatNumber(version.normal_count)}
      />

      <DetailField
        label="Bombing Samples"
        value={formatNumber(version.bombing_count)}
      />

      <DetailField
        label="Created At"
        value={formatDate(version.created_at)}
      />

      <DetailField
        label="Validated At"
        value={formatDate(version.validated_at)}
      />
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Split Distribution                                                        */
/* -------------------------------------------------------------------------- */

function SplitDistribution({ version }) {
  const splitValues = useMemo(
    () =>
      SPLITS.map((split) => ({
        ...split,
        percentage: getSplitPercentage(
          version,
          split.percentageKey
        ),
        count: getSplitCount(version, split.key),
      })),
    [version]
  );

  const availablePercentages = splitValues.filter(
    (split) => split.percentage !== null
  );

  const totalPercentage = availablePercentages.reduce(
    (sum, split) => sum + split.percentage,
    0
  );

  const hasPercentages =
    availablePercentages.length > 0 &&
    totalPercentage > 0;

  const totalSplitCount = splitValues.reduce(
    (sum, split) => sum + (split.count ?? 0),
    0
  );

  const hasCounts = splitValues.some(
    (split) => split.count !== null
  );

  const totalSamples = getTotalSamples(version);

  const percentagesValid =
    availablePercentages.length === SPLITS.length &&
    Math.abs(totalPercentage - 100) < 0.000001;

  return (
    <section className="dataset-details-card">
      <SectionTitle
        icon={Layers}
        title="Split Distribution"
        description="Configured percentages and actual split counts."
      />

      {hasPercentages ? (
        <>
          <div
            className="dataset-version-drawer__split-bar"
            role="img"
            aria-label={splitValues
              .map(
                (split) =>
                  `${split.label} ${split.percentage ?? "unavailable"}%`
              )
              .join(", ")}
          >
            {splitValues.map((split) => {
              if (
                split.percentage === null ||
                split.percentage <= 0
              ) {
                return null;
              }

              return (
                <div
                  key={split.key}
                  className={`dataset-version-drawer__segment dataset-version-drawer__segment--${split.color}`}
                  style={{
                    width: `${split.percentage}%`,
                  }}
                  title={`${split.label}: ${split.percentage}%`}
                />
              );
            })}
          </div>

          <div className="dataset-version-drawer__split-list">
            {splitValues.map((split) => (
              <div
                className="dataset-version-drawer__split-item"
                key={split.key}
              >
                <div className="dataset-version-drawer__split-heading">
                  <i
                    className={`dataset-version-drawer__dot dataset-version-drawer__dot--${split.color}`}
                  />

                  <strong>{split.label}</strong>
                </div>

                <strong>
                  {split.percentage === null
                    ? "—"
                    : `${split.percentage}%`}
                </strong>

                <span>
                  {split.count === null
                    ? "Count unavailable"
                    : `${split.count.toLocaleString()} samples`}
                </span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <EmptyState>
          Split percentages are not available.
        </EmptyState>
      )}

      {hasCounts && (
        <div className="dataset-details-field">
          <span>Split Sample Total</span>
          <strong>{totalSplitCount.toLocaleString()}</strong>
        </div>
      )}

      {totalSamples !== null && hasCounts && (
        <div className="dataset-details-field">
          <span>Dataset Sample Total</span>
          <strong>{totalSamples.toLocaleString()}</strong>
        </div>
      )}

      {hasPercentages && (
        <div
          className={`dataset-version-drawer__split-total ${
            percentagesValid
              ? "dataset-version-drawer__split-total--valid"
              : "dataset-version-drawer__split-total--invalid"
          }`}
        >
          {percentagesValid
            ? "Split percentages total 100%."
            : `Configured total: ${Number(
                totalPercentage.toFixed(2)
              )}%`}
        </div>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Split Configuration                                                        */
/* -------------------------------------------------------------------------- */

function SplitConfiguration({ version }) {
  const configuration = getSplitConfiguration(version);

  return (
    <section className="dataset-details-card">
      <SectionTitle
        icon={Shuffle}
        title="Split Configuration"
        description="Parameters used to create this version."
      />

      <DetailField
        label="Random Seed"
        value={configuration.random_seed}
      />

      <DetailField
        label="Stratified"
        value={configuration.stratified}
      />
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Validation Details                                                         */
/* -------------------------------------------------------------------------- */

function ValidationDetails({ version }) {
  const status = getValidationStatus(version);
  const message = getValidationMessage(version);
  const details = getValidationDetails(version);

  const passed = version.validation_passed === true;
  const failed = version.validation_passed === false;

  return (
    <section className="dataset-details-card">
      <SectionTitle
        icon={ShieldCheck}
        title="Validation"
        description="Dataset version validation result."
      />

      <div
        className={`dataset-version-drawer__validation ${
          passed
            ? "dataset-version-drawer__validation--passed"
            : failed
              ? "dataset-version-drawer__validation--failed"
              : "dataset-version-drawer__validation--pending"
        }`}
      >
        {passed ? (
          <ShieldCheck size={18} />
        ) : (
          <AlertCircle size={18} />
        )}

        <div>
          <strong>
            {passed
              ? "Validation Passed"
              : failed
                ? "Validation Failed"
                : formatStatus(status)}
          </strong>

          {message && (
            <p>{formatValue(message)}</p>
          )}
        </div>
      </div>

      {details.length > 0 && (
        <div className="dataset-version-drawer__validation-details">
          {details.map(([key, value]) => (
            <DetailField
              key={key}
              label={formatStatus(key)}
              value={value}
            />
          ))}
        </div>
      )}

      <DetailField
        label="Validated At"
        value={formatDate(version.validated_at)}
      />
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Feature Schema                                                             */
/* -------------------------------------------------------------------------- */

function FeatureSchema({ version }) {
  const schema = getFeatureSchema(version);
  const features = getFeatures(schema);

  return (
    <section className="dataset-details-card">
      <SectionTitle
        icon={FileText}
        title="Feature Schema"
        description="Feature definitions returned by the backend."
      />

      {schema && (
        <DetailField
          label="Schema Version"
          value={schema.version}
        />
      )}

      {schema && schema.feature_count !== undefined && (
        <DetailField
          label="Feature Count"
          value={schema.feature_count}
        />
      )}

      {features.length > 0 ? (
        <div className="dataset-feature-list">
          {features.map((feature, index) => {
            const key =
              getFeatureKey(feature) ?? `feature-${index}`;

            const description =
              getFeatureDescription(feature);

            return (
              <div
                className="dataset-feature-row"
                key={`${key}-${index}`}
              >
                <div className="dataset-feature-row__identity">
                  <span className="dataset-feature-row__code">
                    {String(key)}
                  </span>

                  <span className="dataset-feature-row__name">
                    {getFeatureName(feature, index)}
                  </span>
                </div>

                {description !== null && (
                  <code className="dataset-feature-row__value">
                    {formatValue(description)}
                  </code>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState>
          No feature definitions are available in this version.
        </EmptyState>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Dataset Version Drawer                                                     */
/* -------------------------------------------------------------------------- */

export default function DatasetVersionDrawer({
  open = false,
  version = null,
  datasets = [],
  loading = false,
  error = null,
  onClose,
  className = "",
}) {
  /* ------------------------------------------------------------------------ */
  /* Body Scroll and Keyboard Handling                                       */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  /* ------------------------------------------------------------------------ */
  /* Close Handler                                                            */
  /* ------------------------------------------------------------------------ */

  const handleBackdropMouseDown = (event) => {
    if (event.target === event.currentTarget) {
      onClose?.();
    }
  };

  /* ------------------------------------------------------------------------ */
  /* Render                                                                   */
  /* ------------------------------------------------------------------------ */

  if (!open) {
    return null;
  }

  const safeDatasets = Array.isArray(datasets)
    ? datasets
    : [];

  const drawerClassName = [
    "dataset-details-drawer",
    "dataset-version-drawer",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className="dataset-drawer-backdrop"
      onMouseDown={handleBackdropMouseDown}
    >
      <aside
        className={drawerClassName}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dataset-version-drawer-title"
      >
        {/* Drawer Header */}
        <header className="dataset-details-drawer__header">
          <div className="dataset-version-drawer__header-title">
            <span className="dataset-details-drawer__eyebrow">
              Dataset Management
            </span>

            <h2 id="dataset-version-drawer-title">
              Version Details
            </h2>

            {version && (
              <span className="dataset-version-drawer__header-name">
                {getVersionNumber(version) !== null
                  ? `v${getVersionNumber(version)}`
                  : getVersionName(version)}
              </span>
            )}
          </div>

          <button
            type="button"
            className="dataset-icon-button"
            onClick={onClose}
            aria-label="Close version details"
            title="Close"
          >
            <X size={20} />
          </button>
        </header>

        {/* Loading State */}
        {loading ? (
          <div
            className="dataset-details-drawer__state"
            role="status"
            aria-live="polite"
          >
            <span className="dataset-spinner" />
            <p>Loading version details...</p>
          </div>
        ) : error ? (
          /* Error State */
          <div
            className="dataset-details-drawer__state dataset-details-drawer__state--error"
            role="alert"
          >
            <AlertCircle size={22} />
            <p>{getErrorMessage(error)}</p>
          </div>
        ) : !version ? (
          /* Empty State */
          <div className="dataset-details-drawer__state">
            <GitBranch size={28} />
            <p>No dataset version selected.</p>
          </div>
        ) : (
          /* Version Details */
          <div className="dataset-details-drawer__body">
            <VersionInformation
              version={version}
              datasets={safeDatasets}
            />

            <SplitDistribution version={version} />

            <SplitConfiguration version={version} />

            <ValidationDetails version={version} />

            <FeatureSchema version={version} />

            <section className="dataset-details-card">
              <SectionTitle
                icon={Calendar}
                title="Version Timeline"
                description="Version creation and validation timestamps."
              />

              <DetailField
                label="Created At"
                value={formatDate(version.created_at)}
              />

              <DetailField
                label="Validated At"
                value={formatDate(version.validated_at)}
              />
            </section>
          </div>
        )}
      </aside>
    </div>
  );
}
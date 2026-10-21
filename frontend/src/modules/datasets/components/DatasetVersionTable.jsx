import {
  Eye,
  GitBranch,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import { WORKSPACE_PAGE_SIZE } from "../types";

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

const DEFAULT_PAGE_SIZE = 30;

/* -------------------------------------------------------------------------- */
/* Version Helpers                                                            */
/* -------------------------------------------------------------------------- */

function getVersionId(version) {
  return version?.id ?? "";
}

function getVersionNumber(version) {
  const value = Number(version?.version_number);

  return Number.isInteger(value) && value > 0
    ? value
    : null;
}

function getVersionName(version) {
  return version?.name ?? "Unnamed Version";
}

function getDatasetId(version) {
  return version?.dataset_id ?? null;
}

function getDatasetName(version, datasets = []) {
  const datasetId = getDatasetId(version);

  if (!datasetId) {
    return "—";
  }

  const dataset = datasets.find(
    (item) => String(item?.id) === String(datasetId)
  );

  return dataset?.name ?? "Unknown Dataset";
}

function getStatus(version) {
  return version?.status ?? "unknown";
}

function formatStatus(status) {
  return String(status)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function getStatusClass(status) {
  return String(status)
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-");
}

function getSampleCount(version) {
  const value = Number(version?.sample_count);

  return Number.isFinite(value) && value >= 0
    ? value
    : null;
}

/* -------------------------------------------------------------------------- */
/* Split Helpers                                                              */
/* -------------------------------------------------------------------------- */

function getSplitPercentage(version, key) {
  const value = version?.[key];

  if (value === null || value === undefined || value === "") {
    return null;
  }

  const percentage = Number(value);

  return Number.isFinite(percentage) &&
    percentage >= 0 &&
    percentage <= 100
    ? percentage
    : null;
}

function formatCount(value) {
  return value === null
    ? "—"
    : value.toLocaleString();
}

/* -------------------------------------------------------------------------- */
/* Split Summary                                                              */
/* -------------------------------------------------------------------------- */

function SplitSummary({ version }) {
  const training = getSplitPercentage(
    version,
    "training_percentage"
  );

  const validation = getSplitPercentage(
    version,
    "validation_percentage"
  );

  const testing = getSplitPercentage(
    version,
    "testing_percentage"
  );

  const percentages = [
    training,
    validation,
    testing,
  ];

  const hasPercentages = percentages.every(
    (value) => value !== null
  );

  const totalPercentage = hasPercentages
    ? percentages.reduce((sum, value) => sum + value, 0)
    : 0;

  const showBar =
    hasPercentages && totalPercentage === 100;

  return (
    <div className="dataset-version-table__split">
      {showBar ? (
        <>
          <div
            className="dataset-version-table__split-bar"
            role="img"
            aria-label={[
              `Training ${training}%`,
              `Validation ${validation}%`,
              `Testing ${testing}%`,
            ].join(", ")}
          >
            {training > 0 && (
              <span
                className="dataset-version-table__split-segment dataset-version-table__split-segment--train"
                style={{ width: `${training}%` }}
                title={`Training: ${training}%`}
              />
            )}

            {validation > 0 && (
              <span
                className="dataset-version-table__split-segment dataset-version-table__split-segment--validation"
                style={{ width: `${validation}%` }}
                title={`Validation: ${validation}%`}
              />
            )}

            {testing > 0 && (
              <span
                className="dataset-version-table__split-segment dataset-version-table__split-segment--test"
                style={{ width: `${testing}%` }}
                title={`Testing: ${testing}%`}
              />
            )}
          </div>

          <div className="dataset-version-table__split-labels">
            <span>Train {training}%</span>
            <span>Val {validation}%</span>
            <span>Test {testing}%</span>
          </div>
        </>
      ) : (
        <span className="dataset-version-table__split-empty">
          Split unavailable
        </span>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Version Table                                                              */
/* -------------------------------------------------------------------------- */

export default function DatasetVersionTable({
  items = [],
  datasets = [],
  loading = false,
  error = "",
  page = 1,
  pageSize = WORKSPACE_PAGE_SIZE || DEFAULT_PAGE_SIZE,
  total = 0,
  totalPages,
  onPageChange,
  onView,
  className = "",
}) {
  const safeItems = Array.isArray(items) ? items : [];
  const safeDatasets = Array.isArray(datasets) ? datasets : [];

  const safePage = Math.max(1, Number(page) || 1);

  const safePageSize = Math.max(
    1,
    Number(pageSize) || DEFAULT_PAGE_SIZE
  );

  const safeTotal = Math.max(
    0,
    Number(total) || 0
  );

  const calculatedPages = Math.max(
    1,
    Math.ceil(safeTotal / safePageSize)
  );

  const pages = Math.max(
    1,
    Number(totalPages) || calculatedPages
  );

  const start =
    safeTotal === 0
      ? 0
      : (safePage - 1) * safePageSize + 1;

  const end = Math.min(
    safePage * safePageSize,
    safeTotal
  );

  const hasPreviousPage = safePage > 1;
  const hasNextPage = safePage < pages;

  const sectionClassName = [
    "dataset-version-table-section",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={sectionClassName}>
      {/* Header */}
      <div className="dataset-version-table-section__header">
        <div>
          <h2>Version History</h2>
          <p>
            Browse immutable dataset versions and their
            training, validation, and testing splits.
          </p>
        </div>

        <span className="dataset-version-table-section__count">
          {safeTotal.toLocaleString()}{" "}
          {safeTotal === 1 ? "version" : "versions"}
        </span>
      </div>

      {/* Table */}
      <div className="dataset-table-container">
        <table className="dataset-table dataset-version-table">
          <thead>
            <tr>
              <th scope="col">Version</th>
              <th scope="col">Dataset</th>
              <th scope="col">Samples</th>
              <th scope="col">Split</th>
              <th scope="col">Status</th>
              <th
                scope="col"
                className="dataset-table__action-column"
              >
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {/* Loading */}
            {loading && (
              <tr>
                <td colSpan={6}>
                  <div
                    className="dataset-table__loading"
                    role="status"
                    aria-live="polite"
                  >
                    <span className="dataset-spinner" />
                    <span>
                      Loading dataset versions...
                    </span>
                  </div>
                </td>
              </tr>
            )}

            {/* Error */}
            {!loading && error && (
              <tr>
                <td colSpan={6}>
                  <div
                    className="dataset-table__empty"
                    role="alert"
                  >
                    <p>{error}</p>
                  </div>
                </td>
              </tr>
            )}

            {/* Empty State */}
            {!loading &&
              !error &&
              safeItems.length === 0 && (
                <tr>
                  <td colSpan={6}>
                    <div className="dataset-table__empty">
                      <GitBranch size={30} />

                      <strong>
                        No dataset versions found
                      </strong>

                      <span>
                        Create a version to define an
                        immutable training, validation,
                        and testing split.
                      </span>
                    </div>
                  </td>
                </tr>
              )}

            {/* Version Rows */}
            {!loading &&
              !error &&
              safeItems.map((version, index) => {
                const id = getVersionId(version);
                const versionNumber =
                  getVersionNumber(version);
                const versionName =
                  getVersionName(version);
                const datasetName =
                  getDatasetName(version, safeDatasets);
                const status = getStatus(version);
                const sampleCount =
                  getSampleCount(version);

                const rowKey =
                  id || `${versionName}-${index}`;

                return (
                  <tr key={rowKey}>
                    {/* Version */}
                    <td>
                      <div className="dataset-version-table__identity">
                        <div className="dataset-version-table__icon">
                          <GitBranch size={18} />
                        </div>

                        <div className="dataset-version-table__identity-text">
                          <strong>
                            {versionNumber !== null
                              ? `v${versionNumber}`
                              : versionName}
                          </strong>

                          <small title={versionName}>
                            {versionName}
                          </small>
                        </div>
                      </div>
                    </td>

                    {/* Dataset */}
                    <td>
                      <span
                        className="dataset-version-table__dataset"
                        title={datasetName}
                      >
                        {datasetName}
                      </span>
                    </td>

                    {/* Samples */}
                    <td>
                      <strong className="dataset-version-table__number">
                        {sampleCount === null
                          ? "—"
                          : sampleCount.toLocaleString()}
                      </strong>
                    </td>

                    {/* Split */}
                    <td>
                      <SplitSummary version={version} />
                    </td>

                    {/* Status */}
                    <td>
                      <span
                        className={`dataset-label dataset-label--${getStatusClass(
                          status
                        )}`}
                      >
                        {formatStatus(status)}
                      </span>
                    </td>

                    {/* Action */}
                    <td className="dataset-table__action-column">
                      <button
                        type="button"
                        className="dataset-version-view"
                        onClick={() => onView?.(version)}
                        disabled={!onView}
                        aria-label={`View ${versionName}`}
                        title="View version details"
                      >
                        <Eye size={17} />
                        <span>View</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {!loading && !error && safeTotal > 0 && (
        <footer className="dataset-table__pagination">
          <span>
            {start.toLocaleString()} - {end.toLocaleString()} / Total{" "}
            {safeTotal.toLocaleString()}
          </span>

          <div className="dataset-table__pagination-actions">
            <button
              type="button"
              className="dataset-icon-button"
              onClick={() =>
                onPageChange?.(safePage - 1)
              }
              disabled={
                !hasPreviousPage || !onPageChange
              }
              aria-label="Previous page"
              title="Previous page"
            >
              <ChevronLeft size={18} aria-hidden="true" />
              <span>Previous</span>
            </button>

            <span className="dataset-table-pagination__page">
              Page {safePage} of {pages}
            </span>

            <button
              type="button"
              className="dataset-icon-button"
              onClick={() =>
                onPageChange?.(safePage + 1)
              }
              disabled={
                !hasNextPage || !onPageChange
              }
              aria-label="Next page"
              title="Next page"
            >
              <span>Next</span>
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </div>
        </footer>
      )}
    </section>
  );
}

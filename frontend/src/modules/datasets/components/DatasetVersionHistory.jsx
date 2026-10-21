import React from "react";

import { DATASET_STATUS_LABELS } from "../types";

/* -------------------------------------------------------------------------- */
/* Formatting                                                                 */
/* -------------------------------------------------------------------------- */

function formatNumber(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return new Intl.NumberFormat().format(number);
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

/* -------------------------------------------------------------------------- */
/* Version Helpers                                                            */
/* -------------------------------------------------------------------------- */

function getVersionId(version) {
  return (
    version?.id ??
    version?.version_id ??
    version?.dataset_version_id ??
    null
  );
}

function getVersionNumber(version) {
  const value =
    version?.version_number ??
    version?.versionNumber ??
    version?.version;

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  return value;
}

function getVersionName(version) {
  return (
    version?.name ??
    version?.version_name ??
    null
  );
}

function getVersionStatus(version) {
  return version?.status ?? "unknown";
}

function getSampleCount(version) {
  return (
    version?.sample_count ??
    version?.sampleCount ??
    version?.total_samples ??
    version?.totalSamples ??
    null
  );
}

function getChangeDescription(version) {
  return (
    version?.change_description ??
    version?.changeDescription ??
    version?.description ??
    null
  );
}

function getIsCurrent(version, currentVersionId) {
  if (
    typeof version?.is_current === "boolean"
  ) {
    return version.is_current;
  }

  if (
    typeof version?.isCurrent === "boolean"
  ) {
    return version.isCurrent;
  }

  const versionId = getVersionId(version);

  return Boolean(
    currentVersionId &&
      versionId &&
      String(versionId) === String(currentVersionId)
  );
}

function getStatusLabel(status) {
  const normalized = String(status ?? "unknown");

  return (
    DATASET_STATUS_LABELS?.[normalized] ??
    DATASET_STATUS_LABELS?.[normalized.toUpperCase()] ??
    normalized
      .replaceAll("_", " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase()
      )
  );
}

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
    "An unexpected error occurred."
  );
}

/* -------------------------------------------------------------------------- */
/* Status                                                                     */
/* -------------------------------------------------------------------------- */

function VersionStatus({ status }) {
  const normalizedStatus = String(
    status ?? "unknown"
  ).toLowerCase();

  return (
    <span
      className={`dataset-version-status dataset-version-status--${normalizedStatus}`}
    >
      {getStatusLabel(status)}
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/* Loading State                                                              */
/* -------------------------------------------------------------------------- */

function LoadingState() {
  return (
    <div
      className="dataset-version-history__loading"
      role="status"
      aria-label="Loading version history"
    >
      {Array.from({ length: 4 }, (_, index) => (
        <div
          key={index}
          className="dataset-version-history__loading-row"
        />
      ))}

      <span className="sr-only">
        Loading version history...
      </span>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Empty State                                                                */
/* -------------------------------------------------------------------------- */

function EmptyState() {
  return (
    <div className="dataset-version-history__empty">
      <h3>No versions found</h3>

      <p>
        This dataset does not have any recorded
        versions yet.
      </p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Error State                                                                */
/* -------------------------------------------------------------------------- */

function ErrorState({ error }) {
  return (
    <div
      className="dataset-version-history__error"
      role="alert"
    >
      <strong>
        Unable to load version history
      </strong>

      <span>{getErrorMessage(error)}</span>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Version Row                                                                */
/* -------------------------------------------------------------------------- */

function VersionRow({
  version,
  currentVersionId,
  onSelectVersion,
}) {
  const versionId = getVersionId(version);
  const versionNumber = getVersionNumber(version);
  const versionName = getVersionName(version);
  const status = getVersionStatus(version);
  const sampleCount = getSampleCount(version);
  const createdAt =
    version?.created_at ??
    version?.createdAt;

  const isCurrent = getIsCurrent(
    version,
    currentVersionId
  );

  const changeDescription =
    getChangeDescription(version);

  const rowKey =
    versionId ??
    versionNumber ??
    `${versionName ?? "version"}-${createdAt ?? ""}`;

  return (
    <tr
      key={rowKey}
      className={
        isCurrent
          ? "dataset-version-history__current-row"
          : ""
      }
    >
      <td>
        <div className="dataset-version-history__version">
          <strong>
            {versionNumber !== null
              ? `v${versionNumber}`
              : "—"}
          </strong>

          {versionName && (
            <span>{versionName}</span>
          )}
        </div>
      </td>

      <td>{formatNumber(sampleCount)}</td>

      <td>
        <VersionStatus status={status} />
      </td>

      <td>
        <span className="dataset-version-history__change">
          {changeDescription ||
            "No change description provided."}
        </span>
      </td>

      <td>{formatDate(createdAt)}</td>

      <td>
        {isCurrent ? (
          <span className="dataset-version-history__current-badge">
            Current
          </span>
        ) : (
          "—"
        )}
      </td>

      <td>
        <button
          type="button"
          className="dataset-button dataset-button--secondary"
          onClick={() => onSelectVersion?.(version)}
          aria-label={`View version ${
            versionNumber !== null
              ? `v${versionNumber}`
              : versionName ?? ""
          }`}
        >
          View
        </button>
      </td>
    </tr>
  );
}

/* -------------------------------------------------------------------------- */
/* Dataset Version History                                                    */
/* -------------------------------------------------------------------------- */

export default function DatasetVersionHistory({
  versions = [],
  currentVersionId = null,
  loading = false,
  error = null,
  onSelectVersion,
}) {
  const safeVersions = Array.isArray(versions)
    ? versions
    : [];

  /* Loading */
  if (loading) {
    return (
      <section
        className="dataset-version-history"
        aria-label="Dataset version history"
      >
        <LoadingState />
      </section>
    );
  }

  /* Error */
  if (error) {
    return (
      <section
        className="dataset-version-history"
        aria-label="Dataset version history"
      >
        <ErrorState error={error} />
      </section>
    );
  }

  /* Empty */
  if (safeVersions.length === 0) {
    return (
      <section
        className="dataset-version-history"
        aria-label="Dataset version history"
      >
        <div className="dataset-version-history__header">
          <div>
            <h2>Version History</h2>
            <p>
              Track dataset versions, sample counts,
              changes, and validation status.
            </p>
          </div>

          <span className="dataset-version-history__count">
            0 versions
          </span>
        </div>

        <EmptyState />
      </section>
    );
  }

  /* Version Table */
  return (
    <section
      className="dataset-version-history"
      aria-label="Dataset version history"
    >
      <div className="dataset-version-history__header">
        <div>
          <h2>Version History</h2>

          <p>
            Track dataset versions, sample counts,
            changes, and validation status.
          </p>
        </div>

        <span className="dataset-version-history__count">
          {formatNumber(safeVersions.length)}{" "}
          {safeVersions.length === 1
            ? "version"
            : "versions"}
        </span>
      </div>

      <div className="dataset-version-history__table-wrapper">
        <table>
          <thead>
            <tr>
              <th scope="col">Version</th>
              <th scope="col">Samples</th>
              <th scope="col">Status</th>
              <th scope="col">Change</th>
              <th scope="col">Created</th>
              <th scope="col">Current</th>
              <th scope="col">Action</th>
            </tr>
          </thead>

          <tbody>
            {safeVersions.map((version, index) => (
              <VersionRow
                key={
                  getVersionId(version) ??
                  getVersionNumber(version) ??
                  index
                }
                version={version}
                currentVersionId={currentVersionId}
                onSelectVersion={onSelectVersion}
              />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
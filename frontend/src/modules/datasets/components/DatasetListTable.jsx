import {
  Eye,
  Database,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
} from "lucide-react";

import {
  DATASET_STATUS_LABELS,
  WORKSPACE_PAGE_SIZE,
} from "../types";

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

function getStatus(dataset) {
  return dataset?.status ?? dataset?.state ?? "active";
}

function getStatusLabel(status) {
  const normalizedStatus = String(status).toLowerCase();

  return (
    DATASET_STATUS_LABELS?.[status] ??
    DATASET_STATUS_LABELS?.[normalizedStatus] ??
    String(status).replaceAll("_", " ")
  );
}

function getDatasetId(dataset) {
  return dataset?.dataset_id ?? dataset?.id ?? null;
}

function getDatasetName(dataset) {
  return dataset?.name ?? dataset?.dataset_name ?? "Untitled Dataset";
}

function getDatasetDescription(dataset) {
  return dataset?.description ?? "";
}

function getSampleCount(dataset) {
  const value =
    dataset?.sample_count ??
    dataset?.email_count ??
    dataset?.total_emails ??
    dataset?.total_samples ??
    0;

  const count = Number(value);
  return Number.isFinite(count) ? Math.max(0, count) : 0;
}

function getVersionCount(dataset) {
  const value = dataset?.version_count ?? dataset?.versions_count ?? 0;
  const count = Number(value);

  return Number.isFinite(count) ? Math.max(0, count) : 0;
}

export default function DatasetListTable({
  items = [],
  loading = false,
  error = "",
  page = 1,
  pageSize = WORKSPACE_PAGE_SIZE || 30,
  total = 0,
  totalPages,
  onPageChange,
  onView,
  onSort,
  sortBy = "created_at",
  sortOrder = "desc",
  className = "",
}) {
  const safeItems = Array.isArray(items) ? items : [];
  const safeTotal = Math.max(0, Number(total) || 0);
  const safePage = Math.max(1, Number(page) || 1);
  const safePageSize = Math.max(1, Number(pageSize) || 30);

  const pages = Math.max(
    1,
    Number(totalPages) ||
      Math.ceil(safeTotal / safePageSize)
  );

  const start =
    safeTotal === 0
      ? 0
      : (safePage - 1) * safePageSize + 1;

  const end = Math.min(
    safePage * safePageSize,
    safeTotal
  );

  const toggleSort = (field) => {
    if (typeof onSort !== "function") {
      return;
    }

    const nextOrder =
      sortBy === field && sortOrder === "asc"
        ? "desc"
        : "asc";

    onSort({
      sort_by: field,
      sort_order: nextOrder,
    });
  };

  const renderEmptyState = () => (
    <div className="dataset-table__empty">
      <Database size={30} aria-hidden="true" />
      <strong>No datasets found</strong>
      <span>
        Create a dataset from the Dataset Workspace.
      </span>
    </div>
  );

  return (
    <section
      className={`dataset-list-table-section ${className}`.trim()}
    >
      <div className="dataset-list-table-section__header">
        <div>
          <h2>Datasets</h2>
          <p>Manage datasets created from eligible emails.</p>
        </div>

        <span className="dataset-list-table-section__count">
          {safeTotal.toLocaleString()} datasets
        </span>
      </div>

      <div className="dataset-table-container">
        <table className="dataset-table dataset-list-table">
          <thead>
            <tr>
              <th scope="col">
                <button
                  type="button"
                  className="dataset-table__sort"
                  onClick={() => toggleSort("name")}
                  disabled={!onSort}
                  aria-label="Sort by dataset name"
                >
                  Dataset
                  <ArrowUpDown size={14} aria-hidden="true" />
                </button>
              </th>

              <th scope="col">Emails</th>

              <th scope="col">Versions</th>

              <th scope="col">Status</th>

              <th scope="col">
                <button
                  type="button"
                  className="dataset-table__sort"
                  onClick={() => toggleSort("created_at")}
                  disabled={!onSort}
                  aria-label="Sort by creation date"
                >
                  Created
                  <ArrowUpDown size={14} aria-hidden="true" />
                </button>
              </th>

              <th
                scope="col"
                className="dataset-table__action-column"
              >
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6}>
                  <div
                    className="dataset-table__loading"
                    role="status"
                    aria-live="polite"
                  >
                    <span className="dataset-spinner" />
                    <span>Loading datasets...</span>
                  </div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={6}>
                  <div className="dataset-table__empty" role="alert">
                    <p>{error}</p>
                  </div>
                </td>
              </tr>
            ) : safeItems.length === 0 ? (
              <tr>
                <td colSpan={6}>{renderEmptyState()}</td>
              </tr>
            ) : (
              safeItems.map((dataset, index) => {
                const id = getDatasetId(dataset);
                const name = getDatasetName(dataset);
                const description = getDatasetDescription(dataset);
                const status = getStatus(dataset);

                return (
                  <tr key={id ?? `dataset-${index}`}>
                    <td>
                      <div className="dataset-list-table__identity">
                        <div className="dataset-list-table__icon">
                          <Database size={18} aria-hidden="true" />
                        </div>

                        <div className="dataset-list-table__name">
                          <strong>{name}</strong>

                          {description && (
                            <span>{description}</span>
                          )}

                          <small>ID: {id ?? "—"}</small>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span className="dataset-list-table__number">
                        {getSampleCount(dataset).toLocaleString()}
                      </span>
                    </td>

                    <td>
                      <span className="dataset-list-table__number">
                        {getVersionCount(dataset).toLocaleString()}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`dataset-label dataset-label--${String(
                          status
                        )
                          .toLowerCase()
                          .replaceAll("_", "-")}`}
                      >
                        {getStatusLabel(status)}
                      </span>
                    </td>

                    <td>{formatDate(dataset?.created_at)}</td>

                    <td className="dataset-table__action-column">
                      <button
                        type="button"
                        className="dataset-button dataset-button--ghost dataset-button--icon"
                        onClick={() => onView?.(dataset)}
                        disabled={!id || typeof onView !== "function"}
                        aria-label={`View ${name}`}
                        title="View dataset details"
                      >
                        <Eye size={17} aria-hidden="true" />
                        <span>View</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

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
              onClick={() => onPageChange?.(safePage - 1)}
              disabled={safePage <= 1}
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
              onClick={() => onPageChange?.(safePage + 1)}
              disabled={safePage >= pages}
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

import { useCallback, useEffect, useRef, useState } from "react";

import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Eye,
  Loader2,
  RefreshCw,
  X,
} from "lucide-react";

import {
  getPreprocessingRuns,
  getPreprocessingErrorMessage,
  normalizeRun,
} from "../services/preprocessingService";

import {
  PREPROCESSING_PAGINATION,
  PREPROCESSING_STATUS,
} from "../types";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: PREPROCESSING_STATUS.PENDING, label: "Pending" },
  { value: PREPROCESSING_STATUS.RUNNING, label: "Running" },
  { value: PREPROCESSING_STATUS.COMPLETED, label: "Completed" },
  { value: PREPROCESSING_STATUS.FAILED, label: "Failed" },
];

const STATUS_LABELS = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

const HIDDEN_DETAIL_KEYS = new Set([
  "id",
  "run_id",
  "status",
  "dataset_version_id",
  "input_count",
  "sample_count",
  "duration_seconds",
  "duration",
  "created_at",
  "started_at",
  "completed_at",
]);

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

function formatDuration(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const seconds = Number(value);

  if (!Number.isFinite(seconds) || seconds < 0) {
    return String(value);
  }

  if (seconds < 60) {
    return `${seconds.toFixed(2)}s`;
  }

  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function formatCount(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const count = Number(value);

  if (!Number.isFinite(count)) {
    return String(value);
  }

  return count.toLocaleString();
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
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

function formatLabel(value) {
  return String(value)
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function getRunId(run) {
  return run?.id ?? run?.run_id ?? "";
}

function getRunStatus(run) {
  return String(run?.status ?? "pending").toLowerCase();
}

function getResponseItems(response) {
  const items =
    response?.items ??
    response?.runs ??
    response?.data?.items ??
    response?.data?.runs ??
    [];

  return Array.isArray(items) ? items.map(normalizeRun) : [];
}

function getResponseTotal(response) {
  const total =
    response?.total ??
    response?.total_count ??
    response?.data?.total ??
    response?.data?.total_count ??
    0;

  const parsed = Number(total);

  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}

function DetailItem({ label, value, code = false }) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  return (
    <div className="preprocessing-detail-item">
      <span className="preprocessing-detail-label">{label}</span>

      {code ? (
        <code className="preprocessing-detail-value preprocessing-detail-code">
          {formatValue(value)}
        </code>
      ) : (
        <span className="preprocessing-detail-value">
          {formatValue(value)}
        </span>
      )}
    </div>
  );
}

function RunDetails({ run }) {
  if (!run) return null;

  const runId = getRunId(run);
  const status = getRunStatus(run);

  const additionalDetails = Object.entries(run).filter(
    ([key, value]) =>
      !HIDDEN_DETAIL_KEYS.has(key) &&
      value !== undefined &&
      value !== null &&
      value !== ""
  );

  return (
    <div className="preprocessing-run-details">
      <div className="preprocessing-detail-status-card">
        <div>
          <span className="preprocessing-detail-label">
            Execution status
          </span>

          <span
            className={`preprocessing-status-badge status-${status}`}
          >
            {STATUS_LABELS[status] ?? status}
          </span>
        </div>

        <div className="preprocessing-detail-status-icon">
          {status === "failed" ? (
            <AlertCircle size={20} />
          ) : (
            <Clock3 size={20} />
          )}
        </div>
      </div>

      <section className="preprocessing-detail-section">
        <h3>Run Information</h3>

        <div className="preprocessing-detail-grid">
          <DetailItem label="Run ID" value={runId} code />
          <DetailItem
            label="Dataset Version ID"
            value={run.dataset_version_id}
            code
          />
          <DetailItem
            label="Input Samples"
            value={formatCount(
              run.input_count ?? run.sample_count
            )}
          />
          <DetailItem
            label="Duration"
            value={formatDuration(
              run.duration_seconds ?? run.duration
            )}
          />
          <DetailItem
            label="Created At"
            value={formatDate(run.created_at)}
          />
          <DetailItem
            label="Started At"
            value={formatDate(run.started_at)}
          />
          <DetailItem
            label="Completed At"
            value={formatDate(run.completed_at)}
          />
        </div>
      </section>

      {(run.error || run.error_message) && (
        <section className="preprocessing-detail-section">
          <h3 className="preprocessing-detail-error-heading">
            <AlertCircle size={16} />
            Error Information
          </h3>

          <pre className="preprocessing-detail-error">
            {formatValue(run.error ?? run.error_message)}
          </pre>
        </section>
      )}

      {additionalDetails.length > 0 && (
        <section className="preprocessing-detail-section">
          <h3>Additional Run Data</h3>

          <div className="preprocessing-detail-grid">
            {additionalDetails.map(([key, value]) => (
              <div
                className="preprocessing-detail-item preprocessing-detail-item-wide"
                key={key}
              >
                <span className="preprocessing-detail-label">
                  {formatLabel(key)}
                </span>

                {typeof value === "object" ? (
                  <pre className="preprocessing-detail-json">
                    {formatValue(value)}
                  </pre>
                ) : (
                  <span className="preprocessing-detail-value">
                    {formatValue(value)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default function PreprocessingHistory({
  datasetVersionId = "",
  onSelectRun,
  selectedRunId = "",
  refreshKey = 0,
}) {
  const [runs, setRuns] = useState([]);
  const [page, setPage] = useState(
    PREPROCESSING_PAGINATION.page
  );
  const pageSize = PREPROCESSING_PAGINATION.page_size;

  const [status, setStatus] = useState("");
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [activeRun, setActiveRun] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const requestIdRef = useRef(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      requestIdRef.current += 1;
    };
  }, []);

  const loadRuns = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError("");

    try {
      const response = await getPreprocessingRuns({
        page,
        pageSize,
        datasetVersionId: datasetVersionId || undefined,
        status: status || undefined,
      });

      if (
        !mountedRef.current ||
        requestId !== requestIdRef.current
      ) {
        return;
      }

      setRuns(getResponseItems(response));
      setTotal(getResponseTotal(response));
    } catch (err) {
      if (
        !mountedRef.current ||
        requestId !== requestIdRef.current
      ) {
        return;
      }

      setRuns([]);
      setTotal(0);
      setError(getPreprocessingErrorMessage(err));
    } finally {
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        setLoading(false);
      }
    }
  }, [page, pageSize, datasetVersionId, status]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns, refreshKey]);

  useEffect(() => {
    if (!drawerOpen) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [drawerOpen]);

  const totalPages = Math.max(
    1,
    Math.ceil(total / pageSize)
  );

  const handleStatusChange = (event) => {
    setStatus(event.target.value);
    setPage(1);
  };

  const handleViewRun = (run) => {
    if (!getRunId(run)) return;

    setActiveRun(run);
    setDrawerOpen(true);
    onSelectRun?.(run);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
  };

  const handlePreviousPage = () => {
    setPage((current) => Math.max(1, current - 1));
  };

  const handleNextPage = () => {
    setPage((current) =>
      Math.min(totalPages, current + 1)
    );
  };

  const isEmpty = !loading && runs.length === 0;

  return (
    <>
      <section className="preprocessing-panel preprocessing-history">
        <div className="preprocessing-panel-heading">
          <div className="preprocessing-heading-icon">
            <Clock3 size={19} aria-hidden="true" />
          </div>

          <div className="preprocessing-heading-copy">
            <h2>Preprocessing History</h2>
            <p>
              Review previous preprocessing runs and their statuses.
            </p>
          </div>

          <button
            type="button"
            className="preprocessing-icon-button"
            onClick={loadRuns}
            disabled={loading}
            aria-label="Refresh preprocessing history"
            title="Refresh"
          >
            {loading ? (
              <Loader2
                size={17}
                className="preprocessing-spinner"
                aria-hidden="true"
              />
            ) : (
              <RefreshCw size={17} aria-hidden="true" />
            )}
          </button>
        </div>

        <div className="preprocessing-history-toolbar">
          <div className="preprocessing-form-field">
            <label htmlFor="preprocessing-history-status">
              Filter by status
            </label>

            <select
              id="preprocessing-history-status"
              value={status}
              onChange={handleStatusChange}
            >
              {STATUS_OPTIONS.map((option) => (
                <option
                  value={option.value}
                  key={option.value || "all"}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="preprocessing-history-total">
            <span>Total runs</span>
            <strong>{total.toLocaleString()}</strong>
          </div>
        </div>

        {error && (
          <div
            className="preprocessing-validation-error"
            role="alert"
          >
            <AlertCircle size={17} aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {loading && runs.length === 0 ? (
          <div className="preprocessing-loading-state">
            <Loader2
              size={22}
              className="preprocessing-spinner"
              aria-hidden="true"
            />
            <span>Loading preprocessing history...</span>
          </div>
        ) : isEmpty ? (
          <div className="preprocessing-empty-state">
            <Clock3 size={22} aria-hidden="true" />
            <p>
              {error
                ? "History could not be loaded."
                : "No preprocessing runs found."}
            </p>
          </div>
        ) : (
          <>
            <div className="preprocessing-history-table-wrapper">
              <table className="preprocessing-history-table">
                <thead>
                  <tr>
                    <th scope="col">Run ID</th>
                    <th scope="col">Status</th>
                    <th scope="col">Dataset Version</th>
                    <th scope="col">Samples</th>
                    <th scope="col">Duration</th>
                    <th scope="col">Created</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>

                <tbody>
                  {runs.map((run, index) => {
                    const runId = getRunId(run);
                    const runStatus = getRunStatus(run);
                    const isSelected =
                      String(selectedRunId || activeRun?.id || activeRun?.run_id) ===
                      String(runId);

                    return (
                      <tr
                        key={runId || `run-${index}`}
                        className={isSelected ? "is-selected" : ""}
                      >
                        <td>
                          <code className="preprocessing-history-run-id">
                            {runId || "—"}
                          </code>
                        </td>

                        <td>
                          <span
                            className={`preprocessing-status-badge status-${runStatus}`}
                          >
                            {STATUS_LABELS[runStatus] ?? runStatus}
                          </span>
                        </td>

                        <td>
                          <code>
                            {run.dataset_version_id ?? "—"}
                          </code>
                        </td>

                        <td>
                          {formatCount(
                            run.input_count ?? run.sample_count
                          )}
                        </td>

                        <td>
                          {formatDuration(
                            run.duration_seconds ?? run.duration
                          )}
                        </td>

                        <td>
                          {formatDate(
                            run.created_at ?? run.started_at
                          )}
                        </td>

                        <td>
                          <button
                            type="button"
                            className="preprocessing-secondary-button preprocessing-view-run-button"
                            onClick={() => handleViewRun(run)}
                            disabled={!runId}
                            aria-label={`View run ${runId}`}
                          >
                            <Eye size={15} aria-hidden="true" />
                            View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="preprocessing-history-pagination">
              <span>
                Page {page} of {totalPages}
              </span>

              <div className="preprocessing-pagination-actions">
                <button
                  type="button"
                  className="preprocessing-icon-button"
                  onClick={handlePreviousPage}
                  disabled={loading || page <= 1}
                  aria-label="Previous page"
                >
                  <ChevronLeft size={17} aria-hidden="true" />
                </button>

                <button
                  type="button"
                  className="preprocessing-icon-button"
                  onClick={handleNextPage}
                  disabled={loading || page >= totalPages}
                  aria-label="Next page"
                >
                  <ChevronRight size={17} aria-hidden="true" />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {drawerOpen && activeRun && (
        <div
          className="preprocessing-drawer-backdrop"
          onClick={handleCloseDrawer}
          role="presentation"
        >
          <aside
            className="preprocessing-details-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="preprocessing-drawer-title"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="preprocessing-drawer-header">
              <div className="preprocessing-drawer-heading">
                <span className="preprocessing-drawer-eyebrow">
                  PREPROCESSING RUN
                </span>
                <h2 id="preprocessing-drawer-title">
                  Run Details
                </h2>
                <p>
                  {getRunId(activeRun)}
                </p>
              </div>

              <button
                type="button"
                className="preprocessing-icon-button preprocessing-drawer-close"
                onClick={handleCloseDrawer}
                aria-label="Close run details"
                title="Close"
              >
                <X size={19} aria-hidden="true" />
              </button>
            </header>

            <div className="preprocessing-drawer-content">
              <RunDetails run={activeRun} />
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
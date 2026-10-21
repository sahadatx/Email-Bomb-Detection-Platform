import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Eye,
  History,
  Loader2,
  Play,
  RefreshCw,
  X,
  XCircle,
} from "lucide-react";

import {
  executePreprocessingRun,
  getPreprocessingRuns,
  getPreprocessingRun,
  getPreprocessingArtifacts,
  getPreprocessingFilters,
  getPreprocessingSummary,
  getPreprocessingErrorMessage,
  normalizeRun,
} from "../services/preprocessingService";

import { PREPROCESSING_PAGINATION } from "../types";

import ExecutionResults from "../components/ExecutionResults";

const PAGE_SIZE = PREPROCESSING_PAGINATION.PAGE_SIZE ?? 30;
const INITIAL_PAGE = PREPROCESSING_PAGINATION.PAGE ?? 1;
const POLL_INTERVAL_MS = 2500;

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
];

const STATUS_LABELS = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

// ----------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------

function getRunId(run) {
  return String(run?.id ?? run?.run_id ?? "");
}

function getRunStatus(run) {
  return String(run?.status ?? "pending").toLowerCase();
}

function getResponseItems(response) {
  const items = response?.items ?? response?.runs ?? [];
  return Array.isArray(items) ? items.map(normalizeRun) : [];
}

function getResponseTotal(response) {
  const total = Number(response?.total ?? 0);
  return Number.isFinite(total) && total >= 0 ? total : 0;
}

function getResponseRun(response) {
  return response?.run ?? response?.data ?? response;
}

function getResponseArtifacts(response) {
  if (Array.isArray(response)) return response;

  const artifacts = response?.items ?? response?.artifacts ?? [];
  return Array.isArray(artifacts) ? artifacts : [];
}

function formatVersion(number, name) {
  const hasNumber =
    number !== undefined && number !== null && number !== "";

  const label = hasNumber
    ? String(number).startsWith("v")
      ? String(number)
      : `v${number}`
    : "";

  if (label && name) return `${label} · ${name}`;
  return label || name || "—";
}

function getDatasetName(run) {
  return run?.dataset_name || "Unknown dataset";
}

function getVersionLabel(run) {
  return formatVersion(
    run?.dataset_version_number,
    run?.dataset_version_name
  );
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString();
}

function formatCount(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);
  return Number.isFinite(number)
    ? number.toLocaleString()
    : String(value);
}

function formatDuration(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const seconds = Number(value);

  if (!Number.isFinite(seconds) || seconds < 0) {
    return String(value);
  }

  if (seconds < 60) return `${seconds.toFixed(2)}s`;

  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

// ----------------------------------------------------------------
// Small components
// ----------------------------------------------------------------

function SummaryCard({ label, value, icon: Icon, tone }) {
  return (
    <article className="preprocessing-summary-card">
      <div className={`preprocessing-summary-icon ${tone}`}>
        <Icon size={19} aria-hidden="true" />
      </div>

      <div className="preprocessing-summary-copy">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function StatusBadge({ status }) {
  const normalized = getRunStatus({ status });

  return (
    <span className={`preprocessing-status-badge status-${normalized}`}>
      {STATUS_LABELS[normalized] ?? normalized}
    </span>
  );
}

function DatasetInfo({ run }) {
  if (!run) return null;

  const rows = [
    ["Dataset", getDatasetName(run)],
    ["Dataset ID", run.dataset_id],
    ["Version", getVersionLabel(run)],
    ["Version ID", run.dataset_version_id],
  ];

  return (
    <section
      className="preprocessing-detail-section"
      style={{ marginBottom: "16px" }}
    >
      <h3>Dataset Information</h3>

      <div className="preprocessing-detail-grid">
        {rows.map(([label, value]) => (
          <div className="preprocessing-detail-item" key={label}>
            <span className="preprocessing-detail-label">{label}</span>
            <span className="preprocessing-detail-value">
              {value || "—"}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

// ----------------------------------------------------------------
// Page
// ----------------------------------------------------------------

export default function PreprocessingHistory() {
  const [runs, setRuns] = useState([]);
  const [page, setPage] = useState(INITIAL_PAGE);

  const [runSearch, setRunSearch] = useState("");
  const [status, setStatus] = useState("");
  const [datasetFilter, setDatasetFilter] = useState("");
  const [versionFilter, setVersionFilter] = useState("");

  const [filterData, setFilterData] = useState([]);

  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState({
    total: 0,
    completed: 0,
    pending: 0,
    failed: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [startingId, setStartingId] = useState("");
  const [startedIds, setStartedIds] = useState(() => new Set());

  const [selectedRun, setSelectedRun] = useState(null);
  const [artifacts, setArtifacts] = useState([]);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);

  const listRequestRef = useRef(0);
  const summaryRequestRef = useRef(0);
  const detailsRequestRef = useRef(0);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      listRequestRef.current += 1;
      summaryRequestRef.current += 1;
      detailsRequestRef.current += 1;
    };
  }, []);

  // --------------------------------------------------------------
  // Loading
  // --------------------------------------------------------------

  const loadFilters = useCallback(async () => {
    try {
      const data = await getPreprocessingFilters();

      if (mountedRef.current) {
        setFilterData(
          Array.isArray(data?.datasets) ? data.datasets : []
        );
      }
    } catch {
      // Filters stay empty; the table still works.
    }
  }, []);

  const loadRuns = useCallback(
    async ({ silent = false } = {}) => {
      const requestId = ++listRequestRef.current;

      if (!silent) {
        setLoading(true);
        setError("");
      }

      try {
        const response = await getPreprocessingRuns({
          page,
          pageSize: PAGE_SIZE,
          status: status || undefined,
          datasetId: datasetFilter || undefined,
          datasetVersionId: versionFilter || undefined,
        });

        if (
          !mountedRef.current ||
          requestId !== listRequestRef.current
        ) {
          return;
        }

        setRuns(getResponseItems(response));
        setTotal(getResponseTotal(response));
      } catch (err) {
        if (
          !mountedRef.current ||
          requestId !== listRequestRef.current ||
          silent
        ) {
          return;
        }

        setRuns([]);
        setTotal(0);
        setError(getPreprocessingErrorMessage(err));
      } finally {
        if (
          mountedRef.current &&
          requestId === listRequestRef.current &&
          !silent
        ) {
          setLoading(false);
        }
      }
    },
    [page, status, datasetFilter, versionFilter]
  );

  const loadSummary = useCallback(async () => {
    const requestId = ++summaryRequestRef.current;

    try {
      const data = await getPreprocessingSummary({
        datasetId: datasetFilter || undefined,
        datasetVersionId: versionFilter || undefined,
      });

      if (
        !mountedRef.current ||
        requestId !== summaryRequestRef.current
      ) {
        return;
      }

      setSummary({
        total: Number(data?.total) || 0,
        completed: Number(data?.completed) || 0,
        pending: Number(data?.pending) || 0,
        failed: Number(data?.failed) || 0,
      });
    } catch {
      // Cards keep their last known values.
    }
  }, [datasetFilter, versionFilter]);

  const loadDetails = useCallback(
    async (run, { silent = false } = {}) => {
      const runId = getRunId(run);
      const requestId = ++detailsRequestRef.current;

      if (!silent) {
        setSelectedRun(run);
        setArtifacts([]);
        setDetailsError("");
        setDetailsLoading(true);
        setDrawerOpen(true);
      }

      if (!runId) {
        setDetailsLoading(false);
        setDetailsError("Selected run does not have a valid ID.");
        return;
      }

      try {
        const [runResponse, artifactResponse] = await Promise.all([
          getPreprocessingRun(runId),
          getPreprocessingArtifacts(runId),
        ]);

        if (
          !mountedRef.current ||
          requestId !== detailsRequestRef.current
        ) {
          return;
        }

        setSelectedRun(
          normalizeRun(getResponseRun(runResponse)) ?? run
        );
        setArtifacts(getResponseArtifacts(artifactResponse));
      } catch (err) {
        if (
          !mountedRef.current ||
          requestId !== detailsRequestRef.current
        ) {
          return;
        }

        if (!silent) {
          setDetailsError(getPreprocessingErrorMessage(err));
        }
      } finally {
        if (
          mountedRef.current &&
          requestId === detailsRequestRef.current &&
          !silent
        ) {
          setDetailsLoading(false);
        }
      }
    },
    []
  );

  useEffect(() => {
    loadFilters();
  }, [loadFilters]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  // --------------------------------------------------------------
  // Auto-refresh while something is running / just started
  // --------------------------------------------------------------

  const hasActiveRuns = useMemo(
    () =>
      runs.some((run) => {
        const runStatus = getRunStatus(run);

        return (
          runStatus === "running" ||
          (runStatus === "pending" && startedIds.has(getRunId(run)))
        );
      }),
    [runs, startedIds]
  );

  useEffect(() => {
    if (!hasActiveRuns) return undefined;

    const timer = setInterval(() => {
      loadRuns({ silent: true });
      loadSummary();
    }, POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [hasActiveRuns, loadRuns, loadSummary]);

  useEffect(() => {
    if (!drawerOpen || !selectedRun) return;

    const latest = runs.find(
      (run) => getRunId(run) === getRunId(selectedRun)
    );

    if (
      latest &&
      getRunStatus(latest) !== getRunStatus(selectedRun)
    ) {
      loadDetails(latest, { silent: true });
    }
  }, [runs, drawerOpen, selectedRun, loadDetails]);

  // --------------------------------------------------------------
  // Filter options (only datasets/versions that have runs)
  // --------------------------------------------------------------

  const datasetOptions = useMemo(
    () =>
      filterData.map((dataset) => ({
        value: String(dataset.id ?? ""),
        label: dataset.name,
      })),
    [filterData]
  );

  const versionOptions = useMemo(() => {
    const source = datasetFilter
      ? filterData.filter(
          (dataset) => String(dataset.id) === datasetFilter
        )
      : filterData;

    return source.flatMap((dataset) =>
      dataset.versions.map((version) => {
        const label = formatVersion(version.number, version.name);

        return {
          value: String(version.id),
          label: datasetFilter
            ? label
            : `${dataset.name} · ${label}`,
        };
      })
    );
  }, [filterData, datasetFilter]);

  const visibleRuns = useMemo(() => {
    const query = runSearch.trim().toLowerCase();

    return runs.filter(
      (run) =>
        !query || getRunId(run).toLowerCase().includes(query)
    );
  }, [runs, runSearch]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const startIndex = total > 0 ? ((page - 1) * PAGE_SIZE) + 1 : 0;
  const endIndex = total > 0 ? Math.min(page * PAGE_SIZE, total) : 0;

  // --------------------------------------------------------------
  // Handlers
  // --------------------------------------------------------------

  const handleStatusChange = (event) => {
    setStatus(event.target.value);
    setPage(1);
  };

  const handleDatasetChange = (event) => {
    setDatasetFilter(event.target.value);
    setVersionFilter("");
    setPage(1);
  };

  const handleVersionChange = (event) => {
    setVersionFilter(event.target.value);
    setPage(1);
  };

  const handleReset = () => {
    setRunSearch("");
    setStatus("");
    setDatasetFilter("");
    setVersionFilter("");
    setPage(1);
  };

  const handleRefresh = () => {
    loadFilters();
    loadRuns();
    loadSummary();
  };

  const handleStartRun = async (run) => {
    const runId = getRunId(run);

    if (!runId || startingId) return;

    setStartingId(runId);
    setError("");

    try {
      await executePreprocessingRun(runId);

      if (!mountedRef.current) return;

      setStartedIds((current) => new Set(current).add(runId));

      await loadRuns({ silent: true });
      loadSummary();
    } catch (err) {
      if (mountedRef.current) {
        setError(getPreprocessingErrorMessage(err));
      }
    } finally {
      if (mountedRef.current) {
        setStartingId("");
      }
    }
  };

  const handleCloseDrawer = () => {
    detailsRequestRef.current += 1;
    setDrawerOpen(false);
    setDetailsLoading(false);
    setDetailsError("");
  };

  const hasFilters = Boolean(
    runSearch || status || datasetFilter || versionFilter
  );

  // --------------------------------------------------------------
  // Render
  // --------------------------------------------------------------

  return (
    <main className="preprocessing-history-page">
      <header className="preprocessing-workspace-header">
        <div className="preprocessing-workspace-title">
          <div className="preprocessing-workspace-icon">
            <History size={25} aria-hidden="true" />
          </div>

          <div>
            <div className="preprocessing-workspace-eyebrow">
              MODULE 06 / HISTORY
            </div>

            <h1>Preprocessing History</h1>

            <p>Review and inspect previous preprocessing runs.</p>
          </div>
        </div>

        <button
          type="button"
          className="preprocessing-secondary-button"
          onClick={handleRefresh}
          disabled={loading}
        >
          {loading ? (
            <Loader2
              size={16}
              className="preprocessing-spinner"
              aria-hidden="true"
            />
          ) : (
            <RefreshCw size={16} aria-hidden="true" />
          )}
          Refresh
        </button>
      </header>

      <section className="preprocessing-history-summary">
        <SummaryCard
          label="Total Runs"
          value={summary.total.toLocaleString()}
          icon={History}
          tone="neutral"
        />

        <SummaryCard
          label="Completed"
          value={summary.completed.toLocaleString()}
          icon={CheckCircle2}
          tone="success"
        />

        <SummaryCard
          label="Pending"
          value={summary.pending.toLocaleString()}
          icon={Clock3}
          tone="warning"
        />

        <SummaryCard
          label="Failed"
          value={summary.failed.toLocaleString()}
          icon={XCircle}
          tone="danger"
        />
      </section>

      <section className="preprocessing-panel preprocessing-history-page-panel">
        <div className="preprocessing-panel-heading">
          <div className="preprocessing-heading-icon">
            <History size={19} aria-hidden="true" />
          </div>

          <div className="preprocessing-heading-copy">
            <h2>Filters</h2>
            <p>Filter persisted preprocessing runs.</p>
          </div>
        </div>

        <div className="preprocessing-history-toolbar">
          <div className="preprocessing-form-field">
            <label htmlFor="history-run-search">Search Run ID</label>
            <input
              id="history-run-search"
              type="search"
              value={runSearch}
              onChange={(event) => setRunSearch(event.target.value)}
              placeholder="Search by run ID..."
            />
          </div>

          <div className="preprocessing-form-field">
            <label htmlFor="history-status-filter">Run Status</label>
            <select
              id="history-status-filter"
              value={status}
              onChange={handleStatusChange}
            >
              {STATUS_OPTIONS.map((option) => (
                <option
                  key={option.value || "all"}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="preprocessing-form-field">
            <label htmlFor="history-dataset-filter">Dataset</label>
            <select
              id="history-dataset-filter"
              value={datasetFilter}
              onChange={handleDatasetChange}
            >
              <option value="">All datasets</option>
              {datasetOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="preprocessing-form-field">
            <label htmlFor="history-version-filter">
              Dataset Version
            </label>
            <select
              id="history-version-filter"
              value={versionFilter}
              onChange={handleVersionChange}
            >
              <option value="">All versions</option>
              {versionOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

        </div>
        <div className="preprocessing-history-filter-actions">
          <span>{hasFilters ? "Filters applied to preprocessing history." : "Filter persisted preprocessing runs."}</span>
          <button type="button" className="preprocessing-secondary-button" onClick={handleReset} disabled={!hasFilters}>Reset Filters</button>
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

        <div className="preprocessing-panel-heading preprocessing-runs-heading">
          <div className="preprocessing-heading-copy">
            <h2>Preprocessing Runs</h2>
            <p>Run status and execution details</p>
          </div>

          <span className="preprocessing-api-indicator">
            API data
          </span>
        </div>

        {loading && runs.length === 0 ? (
          <div className="preprocessing-loading-state">
            <Loader2
              size={22}
              className="preprocessing-spinner"
              aria-hidden="true"
            />
            <span>Loading preprocessing runs...</span>
          </div>
        ) : visibleRuns.length === 0 ? (
          <div className="preprocessing-empty-state">
            <History size={22} aria-hidden="true" />
            <p>
              {error
                ? "Preprocessing history could not be loaded."
                : hasFilters
                  ? "No runs match the selected filters."
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
                    <th scope="col">Dataset / Version</th>
                    <th scope="col">Status</th>
                    <th scope="col">Samples</th>
                    <th scope="col">Duration</th>
                    <th scope="col">Created</th>
                    <th scope="col">Action</th>
                  </tr>
                </thead>

                <tbody>
                  {visibleRuns.map((run, index) => {
                    const runId = getRunId(run);
                    const runStatus = getRunStatus(run);
                    const isSelected =
                      getRunId(selectedRun) === runId;
                    const isStarting = startingId === runId;

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
                          <div className="preprocessing-dataset-cell">
                            <span>{getDatasetName(run)}</span>
                            <small>{getVersionLabel(run)}</small>
                          </div>
                        </td>

                        <td>
                          <StatusBadge status={runStatus} />
                        </td>

                        <td>{formatCount(run.input_count)}</td>

                        <td>{formatDuration(run.duration_seconds)}</td>

                        <td>{formatDate(run.created_at)}</td>

                        <td>
                          <div
                            style={{
                              display: "flex",
                              gap: "8px",
                              alignItems: "center",
                            }}
                          >
                            {runStatus === "pending" && (
                              <button
                                type="button"
                                className="preprocessing-secondary-button preprocessing-view-run-button"
                                onClick={() => handleStartRun(run)}
                                disabled={Boolean(startingId)}
                              >
                                {isStarting ? (
                                  <Loader2
                                    size={15}
                                    className="preprocessing-spinner"
                                    aria-hidden="true"
                                  />
                                ) : (
                                  <Play size={15} aria-hidden="true" />
                                )}
                                Start
                              </button>
                            )}

                            <button
                              type="button"
                              className="preprocessing-secondary-button preprocessing-view-run-button"
                              onClick={() => loadDetails(run)}
                              disabled={!runId}
                            >
                              <Eye size={15} aria-hidden="true" />
                              View
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {!loading && total > 0 && (
              <div className="email-pagination" aria-label="Preprocessing history pagination">
                <div className="email-pagination-summary">
                  <span>{startIndex} - {endIndex}</span>
                  <span>/ Total {total.toLocaleString()}</span>
                </div>

                <div className="email-pagination-controls">
                  <button
                    type="button"
                    className="email-pagination-button"
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    disabled={loading || page <= 1}
                    aria-label="Go to previous page"
                  >
                    <span aria-hidden="true">‹</span>
                    Previous
                  </button>

                  <span className="email-pagination-page">
                    Page <strong>{page}</strong> of <strong>{totalPages}</strong>
                  </span>

                  <button
                    type="button"
                    className="email-pagination-button"
                    onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                    disabled={loading || page >= totalPages}
                    aria-label="Go to next page"
                  >
                    Next
                    <span aria-hidden="true">›</span>
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {drawerOpen && (
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
            <div className="preprocessing-drawer-header">
              <div>
                <span className="preprocessing-workspace-eyebrow">
                  PREPROCESSING RUN
                </span>

                <h2 id="preprocessing-drawer-title">Run Details</h2>

                <p>{getRunId(selectedRun) || "Selected run"}</p>
              </div>

              <button
                type="button"
                className="preprocessing-icon-button"
                onClick={handleCloseDrawer}
                aria-label="Close run details"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>

            <div className="preprocessing-drawer-content">
              <DatasetInfo run={selectedRun} />

              <ExecutionResults
                run={selectedRun}
                artifacts={artifacts}
                loading={detailsLoading}
                error={detailsError}
              />
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}

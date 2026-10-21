
import { Eye } from "lucide-react";
import { TRAINING_STATUS_LABELS } from "../types";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString();
}

function formatDuration(value) {
  if (value == null) return "—";

  if (value < 1000) return `${value} ms`;

  const seconds = Math.floor(value / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  return `${remainingSeconds}s`;
}

function StatusBadge({ status }) {
  const normalized = String(status || "pending").toLowerCase();

  return (
    <span
      className={`ml-status-badge ml-status-badge--${normalized}`}
    >
      {TRAINING_STATUS_LABELS?.[normalized] || normalized}
    </span>
  );
}

export default function TrainingRunTable({
  runs = [],
  loading = false,
  error = "",
  hasFilters = false,
  onView,
  onResume,
  onRefresh,
}) {
  if (loading && runs.length === 0) {
    return (
      <div className="ml-training-table__state">
        <span className="ml-loading-spinner" />
        <p>Loading training runs...</p>
      </div>
    );
  }

  if (error && runs.length === 0) {
    return (
      <div className="ml-training-table__state ml-training-table__state--error">
        <p>{error}</p>
        <button
          type="button"
          className="ml-button ml-button--secondary"
          onClick={onRefresh}
        >
          Retry
        </button>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="ml-training-table__state">
        <h3>{hasFilters ? "No runs match these filters" : "No training runs found"}</h3>
        <p>{hasFilters ? "Change or clear the filters to see other runs." : "Create a training run to get started."}</p>
      </div>
    );
  }

  return (
    <div className="ml-training-table__wrapper">
      {error && (
        <div className="ml-inline-error" role="alert">
          {error}
        </div>
      )}

      <div className="ml-training-table__scroll">
        <table className="ml-training-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Model</th>
              <th>Status</th>
              <th>Preprocessing Run</th>
              <th>Dataset Version</th>
              <th>Progress</th>
              <th>Started At</th>
              <th>Duration</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {runs.map((run) => (
              <tr key={run.id}>
                <td><code>{String(run.id).slice(0, 13)}</code></td>
                <td>{run.model_name || run.model_definition_id || "—"}</td>

                <td>
                  <StatusBadge status={run.status} />
                </td>

                <td>
                  <code>{String(run.preprocessing_run_id || "—").slice(0, 13)}</code>
                </td>
                <td className="ml-training-table__dataset-version" title={run.preprocessing?.dataset_name ? `${run.preprocessing.dataset_name} · v${run.preprocessing.dataset_version_number ?? "—"}` : run.preprocessing?.dataset_version_id || "—"}>{run.preprocessing?.dataset_name ? `${run.preprocessing.dataset_name} · v${run.preprocessing.dataset_version_number ?? "—"}` : run.preprocessing?.dataset_version_id || "—"}</td>
                <td>
                  <div className="ml-training-table__progress">
                    <div className="ml-progress-track">
                      <div
                        className="ml-progress-fill"
                        style={{
                          width: `${Math.min(100, Math.max(0, Number(run.progress_percent) || 0))}%`,
                        }}
                      />
                    </div>
                    <span>{Math.min(100, Math.max(0, Number(run.progress_percent) || 0))}%</span>
                  </div>
                </td>
                <td>{formatDate(run.started_at)}</td>
                <td>{formatDuration(run.duration_ms)}</td>

                <td>
                  {run.status === "pending" && (
                    <button
                      type="button"
                      className="ml-button ml-button--small ml-button--secondary ml-training-view-button"
                      onClick={() => onResume?.(run)}
                    >
                      Start
                    </button>
                  )}{" "}
                  <button
                    type="button"
                    className="ml-button ml-button--small ml-button--secondary ml-training-view-button"
                    onClick={() => onView?.(run)}
                  >
                    <Eye size={14} aria-hidden="true" />
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

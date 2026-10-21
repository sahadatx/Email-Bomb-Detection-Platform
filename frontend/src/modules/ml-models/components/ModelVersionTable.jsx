
import { Eye } from "lucide-react";
import {
  MODEL_VERSION_STATUS_LABELS,
} from "../types";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function formatSize(bytes) {
  if (bytes == null) return "—";
  if (bytes === 0) return "0 Bytes";

  const units = ["Bytes", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(bytes / 1024 ** index).toFixed(2)} ${units[index]}`;
}

function VersionStatusBadge({ status }) {
  const normalized = String(status || "registered").toLowerCase();

  return (
    <span
      className={`ml-version-status ml-version-status--${normalized}`}
    >
      {MODEL_VERSION_STATUS_LABELS?.[normalized] || normalized}
    </span>
  );
}

export default function ModelVersionTable({
  versions = [],
  loading = false,
  error = "",
  onView,
  onActivate,
  onArchive,
  onRefresh,
  actionLoadingId = null,
}) {
  if (loading && versions.length === 0) {
    return (
      <div className="ml-version-table__state">
        <span className="ml-loading-spinner" />
        <p>Loading model versions...</p>
      </div>
    );
  }

  if (error && versions.length === 0) {
    return (
      <div className="ml-version-table__state ml-version-table__state--error">
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

  if (versions.length === 0) {
    return (
      <div className="ml-version-table__state">
        <h3>No model versions found</h3>
        <p>Completed training runs can produce model versions.</p>
      </div>
    );
  }

  return (
    <div className="ml-version-table__wrapper">
      {error && (
        <div className="ml-inline-error" role="alert">
          {error}
        </div>
      )}

      <div className="ml-version-table__scroll">
        <table className="ml-version-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Model Definition</th>
              <th>Status</th>
              <th>Artifact</th>
              <th>Size</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {versions.map((version) => {
              const busy = actionLoadingId === version.id;
              const status = String(version.status || "").toLowerCase();

              return (
                <tr key={version.id}>
                  <td>
                    <div className="ml-version-table__identity">
                      <strong>{version.version || "—"}</strong>
                      <small>{version.id}</small>
                    </div>
                  </td>

                  <td>
                    <span className="ml-version-table__uuid">
                      {version.model_definition_id || "—"}
                    </span>
                  </td>

                  <td>
                    <VersionStatusBadge status={status} />
                  </td>

                  <td>
                    <span
                      className="ml-version-table__artifact"
                      title={version.artifact_filename || ""}
                    >
                      {version.artifact_filename || "—"}
                    </span>
                  </td>

                  <td>{formatSize(version.size_bytes)}</td>
                  <td>{formatDate(version.created_at)}</td>

                  <td>
                    <div className="ml-version-table__actions">
                      <button
                        type="button"
                        className="ml-button ml-button--small ml-button--secondary"
                        onClick={() => onView?.(version)}
                      >
                        <Eye size={14} aria-hidden="true" />
                        View
                      </button>

                      {status === "registered" && (
                        <button
                          type="button"
                          className="ml-button ml-button--small ml-button--primary"
                          disabled={busy}
                          onClick={() => onActivate?.(version)}
                        >
                          {busy ? "Working..." : "Activate"}
                        </button>
                      )}

                      {status === "active" && (
                        <span className="ml-version-table__current">
                          Current
                        </span>
                      )}

                      {status !== "archived" && (
                        <button
                          type="button"
                          className="ml-button ml-button--small ml-button--danger"
                          disabled={busy}
                          onClick={() => onArchive?.(version)}
                        >
                          {busy ? "Working..." : "Archive"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

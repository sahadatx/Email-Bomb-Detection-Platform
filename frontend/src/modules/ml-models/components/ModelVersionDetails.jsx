
import { MODEL_VERSION_STATUS_LABELS } from "../types";

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

function DetailItem({ label, value, monospace = false }) {
  return (
    <div className="ml-version-detail__item">
      <span>{label}</span>
      <strong className={monospace ? "is-monospace" : ""}>
        {value ?? "—"}
      </strong>
    </div>
  );
}

export default function VersionDetails({
  version,
  onClose,
  onActivate,
  onArchive,
  actionLoading = false,
}) {
  if (!version) return null;

  const status = String(version.status || "registered").toLowerCase();

  return (
    <section className="ml-version-details">
      <header className="ml-version-details__header">
        <div>
          <span className="ml-version-details__eyebrow">
            MODEL REGISTRY
          </span>
          <h2>Version {version.version || "—"}</h2>
          <p>Model version information and artifact metadata.</p>
        </div>

        <button
          type="button"
          className="ml-button ml-button--secondary"
          onClick={onClose}
          aria-label="Close version details"
        >
          Close
        </button>
      </header>

      <div className="ml-version-details__status-row">
        <span className={`ml-version-status ml-version-status--${status}`}>
          {MODEL_VERSION_STATUS_LABELS?.[status] || status}
        </span>
      </div>

      <div className="ml-version-details__grid">
        <DetailItem label="Version ID" value={version.id} monospace />
        <DetailItem
          label="Model Definition ID"
          value={version.model_definition_id}
          monospace
        />
        <DetailItem
          label="Training Run ID"
          value={version.training_run_id}
          monospace
        />
        <DetailItem label="Version" value={version.version} />
        <DetailItem
          label="Artifact Filename"
          value={version.artifact_filename}
        />
        <DetailItem
          label="Media Type"
          value={version.media_type}
        />
        <DetailItem
          label="Artifact Size"
          value={formatSize(version.size_bytes)}
        />
        <DetailItem
          label="Created At"
          value={formatDate(version.created_at)}
        />
        <DetailItem
          label="Activated At"
          value={formatDate(version.activated_at)}
        />
        <DetailItem
          label="Archived At"
          value={formatDate(version.archived_at)}
        />
        <DetailItem
          label="Storage Path"
          value={version.storage_path}
          monospace
        />
        <DetailItem
          label="SHA-256 Checksum"
          value={version.checksum_sha256}
          monospace
        />
      </div>

      <div className="ml-version-details__metadata">
        <h3>Version Metadata</h3>
        {version.metadata_json &&
        Object.keys(version.metadata_json).length > 0 ? (
          <pre>
            {JSON.stringify(version.metadata_json, null, 2)}
          </pre>
        ) : (
          <p>No metadata available.</p>
        )}
      </div>

      <footer className="ml-version-details__actions">
        {status === "registered" && (
          <button
            type="button"
            className="ml-button ml-button--primary"
            disabled={actionLoading}
            onClick={() => onActivate?.(version)}
          >
            {actionLoading ? "Activating..." : "Activate Version"}
          </button>
        )}

        {status !== "archived" && (
          <button
            type="button"
            className="ml-button ml-button--danger"
            disabled={actionLoading}
            onClick={() => onArchive?.(version)}
          >
            {actionLoading ? "Archiving..." : "Archive Version"}
          </button>
        )}

        <button
          type="button"
          className="ml-button ml-button--secondary"
          onClick={onClose}
          disabled={actionLoading}
        >
          Close
        </button>
      </footer>
    </section>
  );
}
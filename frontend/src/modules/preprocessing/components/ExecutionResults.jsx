import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  FileArchive,
  FileText,
  Loader2,
  Package,
} from "lucide-react";

const STATUS_LABELS = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    return value.toLocaleString();
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
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
    return `${seconds.toFixed(2)} seconds`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  return `${minutes}m ${remainingSeconds}s`;
}

function getStatusIcon(status) {
  switch (status) {
    case "completed":
      return <CheckCircle2 size={17} />;

    case "failed":
      return <AlertCircle size={17} />;

    case "running":
      return (
        <Loader2
          size={17}
          className="preprocessing-spinner"
        />
      );

    default:
      return <Clock3 size={17} />;
  }
}

function getStatusLabel(status) {
  return STATUS_LABELS[status] ?? status;
}

function getRunId(run) {
  return run.id ?? run.run_id ?? "—";
}

function getSummary(run) {
  const summary = run.result_summary;

  if (
    summary &&
    typeof summary === "object" &&
    !Array.isArray(summary)
  ) {
    return summary;
  }

  return {};
}

function formatSummaryValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  }

  return formatValue(value);
}

function getArtifactKey(artifact, index) {
  return (
    artifact.id ??
    artifact.filename ??
    artifact.artifact_type ??
    `artifact-${index}`
  );
}

function getArtifactName(artifact) {
  return (
    artifact.filename ??
    artifact.artifact_type ??
    "Artifact"
  );
}

function getArtifactSize(artifact) {
  if (artifact.size_bytes === null || artifact.size_bytes === undefined) {
    return "Size unavailable";
  }

  const size = Number(artifact.size_bytes);

  if (!Number.isFinite(size) || size < 0) {
    return "Size unavailable";
  }

  return `${size.toLocaleString()} bytes`;
}

export default function ExecutionResults({
  run = null,
  artifacts = [],
  loading = false,
  error = "",
}) {
  if (loading) {
    return (
      <section className="preprocessing-panel preprocessing-execution-results">
        <div className="preprocessing-loading-state">
          <Loader2
            size={22}
            className="preprocessing-spinner"
            aria-hidden="true"
          />
          <span>Loading execution results...</span>
        </div>
      </section>
    );
  }

  if (!run) {
    return (
      <section className="preprocessing-panel preprocessing-execution-results">
        <div className="preprocessing-panel-heading">
          <div className="preprocessing-heading-icon">
            <FileText size={19} aria-hidden="true" />
          </div>

          <div className="preprocessing-heading-copy">
            <h2>Execution Results</h2>
            <p>Run summary and generated artifacts.</p>
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

        <div className="preprocessing-empty-state">
          <Package size={22} aria-hidden="true" />
          <p>Select a preprocessing run to view its results.</p>
        </div>
      </section>
    );
  }

  const status = String(run.status ?? "pending").toLowerCase();
  const summary = getSummary(run);
  const runArtifacts = Array.isArray(artifacts) ? artifacts : [];
  const classDistribution =
    summary.class_distribution &&
    typeof summary.class_distribution === "object" &&
    !Array.isArray(summary.class_distribution)
      ? summary.class_distribution
      : null;
  const splitLabels = [
    ["train", "Training"],
    ["validation", "Validation"],
    ["test", "Test"],
  ];
  const hasClassDistribution = classDistribution &&
    splitLabels.some(([key]) => classDistribution[key]);

  return (
    <section className="preprocessing-panel preprocessing-execution-results">
      <div className="preprocessing-panel-heading">
        <div className="preprocessing-heading-icon">
          <FileText size={19} aria-hidden="true" />
        </div>

        <div className="preprocessing-heading-copy">
          <h2>Execution Results</h2>
          <p>Preprocessing run summary and artifacts.</p>
        </div>

        <span
          className={`preprocessing-status-badge status-${status}`}
        >
          {getStatusIcon(status)}
          {getStatusLabel(status)}
        </span>
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

      <div className="preprocessing-results-grid">
        <div className="preprocessing-result-card">
          <span>Run ID</span>
          <strong className="preprocessing-result-id">
            {formatValue(getRunId(run))}
          </strong>
        </div>

        <div className="preprocessing-result-card">
          <span>Dataset version ID</span>
          <strong className="preprocessing-result-id">
            {formatValue(run.dataset_version_id)}
          </strong>
        </div>

        <div className="preprocessing-result-card">
          <span>Input samples</span>
          <strong>
            {formatValue(
              run.input_count ??
                run.sample_count ??
                summary.input_count
            )}
          </strong>
        </div>

        <div className="preprocessing-result-card">
          <span>Output samples</span>
          <strong>
            {formatValue(
              run.output_count ?? summary.output_count
            )}
          </strong>
        </div>

        <div className="preprocessing-result-card">
          <span>Features</span>
          <strong>
            {formatValue(
              run.feature_count ?? summary.feature_count
            )}
          </strong>
        </div>

        <div className="preprocessing-result-card">
          <span>Duration</span>
          <strong>
            {formatDuration(
              run.duration_seconds ?? run.duration
            )}
          </strong>
        </div>
      </div>

      {status === "failed" && (
        <div
          className="preprocessing-validation-error"
          role="alert"
        >
          <AlertCircle size={17} aria-hidden="true" />

          <div>
            <strong>Preprocessing failed</strong>

            <p>
              {run.error_message ??
                run.error ??
                "The backend did not provide an error message."}
            </p>

            {run.error_code && (
              <small>Error code: {run.error_code}</small>
            )}
          </div>
        </div>
      )}

      {status === "completed" && (
        <div className="preprocessing-validation-success">
          <CheckCircle2 size={17} aria-hidden="true" />
          <span>
            Backend reports that this run completed.
          </span>
        </div>
      )}

      {hasClassDistribution && (
        <div className="preprocessing-results-section">
          <div className="preprocessing-config-section-heading">
            <div>
              <h3>Class Distribution by Split</h3>
              <p>Counts from the processed artifacts’ ground-truth labels.</p>
            </div>
          </div>
          <div className="preprocessing-class-distribution-wrap">
            <table className="preprocessing-class-distribution">
              <thead>
                <tr>
                  <th scope="col">Split</th>
                  <th scope="col">Normal</th>
                  <th scope="col">Bombing</th>
                  <th scope="col">Total</th>
                </tr>
              </thead>
              <tbody>
                {splitLabels.map(([key, label]) => {
                  const counts = classDistribution[key] ?? {};
                  const normal = Number(counts.normal ?? 0);
                  const bombing = Number(counts.bombing ?? 0);
                  return (
                    <tr key={key}>
                      <th scope="row">{label}</th>
                      <td>{formatValue(normal)}</td>
                      <td>{formatValue(bombing)}</td>
                      <td>{formatValue(normal + bombing)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="preprocessing-results-section">
        <div className="preprocessing-config-section-heading">
          <div>
            <h3>Result Summary</h3>
            <p>Summary fields returned by the backend.</p>
          </div>
        </div>

        {Object.keys(summary).length === 0 ? (
          <div className="preprocessing-empty-state compact">
            <p>No result summary is available for this run.</p>
          </div>
        ) : (
          <dl className="preprocessing-summary-list">
            {Object.entries(summary).map(([key, value]) => (
              <div
                className="preprocessing-summary-row"
                key={key}
              >
                <dt>{key.replaceAll("_", " ")}</dt>
                <dd>{formatSummaryValue(value)}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>

      <div className="preprocessing-results-section">
        <div className="preprocessing-config-section-heading">
          <div>
            <h3>Artifacts</h3>
            <p>Files and metadata associated with this run.</p>
          </div>

          <span className="preprocessing-config-count">
            {runArtifacts.length}
          </span>
        </div>

        {runArtifacts.length === 0 ? (
          <div className="preprocessing-empty-state compact">
            <FileArchive size={20} aria-hidden="true" />
            <p>No artifacts are available for this run.</p>
          </div>
        ) : (
          <div className="preprocessing-artifact-list">
            {runArtifacts.map((artifact, index) => (
              <article
                className="preprocessing-artifact-item"
                key={getArtifactKey(artifact, index)}
              >
                <div className="preprocessing-artifact-icon">
                  <FileArchive size={18} aria-hidden="true" />
                </div>

                <div className="preprocessing-artifact-copy">
                  <strong>{getArtifactName(artifact)}</strong>

                  <small>
                    {artifact.artifact_type ?? "File"}
                    {artifact.media_type
                      ? ` · ${artifact.media_type}`
                      : ""}
                  </small>
                </div>

                <div className="preprocessing-artifact-size">
                  {getArtifactSize(artifact)}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

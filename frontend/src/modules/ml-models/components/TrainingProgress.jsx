
import { TRAINING_STATUS_LABELS } from "../types";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

export default function TrainingProgress({ run }) {
  if (!run) {
    return (
      <div className="ml-training-progress__empty">
        Select a training run to view its progress.
      </div>
    );
  }

  const status = String(run.status || "pending").toLowerCase();
  const progress = Math.min(
    100,
    Math.max(0, Number(run.progress_percent) || 0)
  );

  const isActive = ["queued", "running"].includes(status);
  const isComplete = status === "completed";
  const isFailed = status === "failed";
  const isCancelled = status === "cancelled";

  return (
    <section className="ml-training-progress">
      <div className="ml-training-progress__header">
        <div>
          <h3>Training Progress</h3>
          <p className="ml-training-progress__id">{run.id}</p>
        </div>

        <span
          className={`ml-status-badge ml-status-badge--${status}`}
        >
          {TRAINING_STATUS_LABELS?.[status] || status}
        </span>
      </div>

      <div className="ml-training-progress__meter">
        <div className="ml-training-progress__meter-label">
          <span>Progress</span>
          <strong>{progress}%</strong>
        </div>

        <div
          className="ml-progress-track ml-progress-track--large"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Training progress"
        >
          <div
            className={`ml-progress-fill ${
              isFailed ? "ml-progress-fill--failed" : ""
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {isActive && (
          <p className="ml-training-progress__message">
            {status === "queued"
              ? "Training run is queued."
              : "Training run is marked as running."}
          </p>
        )}

        {isComplete && (
          <p className="ml-training-progress__message ml-training-progress__message--success">
            Training run completed.
          </p>
        )}

        {isFailed && (
          <p className="ml-training-progress__message ml-training-progress__message--error">
            {run.error_message || "Training run failed."}
          </p>
        )}

        {isCancelled && (
          <p className="ml-training-progress__message">
            Training run was cancelled.
          </p>
        )}

        {status === "pending" && (
          <p className="ml-training-progress__message">
            Waiting for the training process to start.
          </p>
        )}
      </div>

      <div className="ml-training-progress__stats">
        <div>
          <span>Training Samples</span>
          <strong>{run.training_sample_count ?? "—"}</strong>
        </div>
        <div>
          <span>Validation Samples</span>
          <strong>{run.validation_sample_count ?? "—"}</strong>
        </div>
        <div>
          <span>Duration</span>
          <strong>
            {run.duration_ms == null
              ? "—"
              : `${(run.duration_ms / 1000).toFixed(2)}s`}
          </strong>
        </div>
      </div>

      <div className="ml-training-progress__timestamps">
        <div>
          <span>Started</span>
          <strong>{formatDate(run.started_at)}</strong>
        </div>
        <div>
          <span>Completed</span>
          <strong>{formatDate(run.completed_at)}</strong>
        </div>
      </div>

      {run.error_code && (
        <div className="ml-training-progress__error">
          <strong>Error code:</strong> {run.error_code}
        </div>
      )}
    </section>
  );
}
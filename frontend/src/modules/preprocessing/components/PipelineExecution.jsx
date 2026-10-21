import { useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  CirclePlay,
  Loader2,
} from "lucide-react";

import {
  createPreprocessingRun,
  getPreprocessingErrorMessage,
} from "../services/preprocessingService";

// ============================================================================
// HELPERS
// ============================================================================

function normalizeRun(response) {
  return (
    response?.run ??
    response?.data?.run ??
    response?.data ??
    response
  );
}

function getRunId(run) {
  return run?.id ?? run?.run_id ?? null;
}

function formatError(error) {
  return getPreprocessingErrorMessage(error);
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function PipelineExecution({
  datasetVersionId = "",
  config,
  disabled = false,
  onRunCreated,
  configurationValidated = false,
  canManage = true,
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdRun, setCreatedRun] = useState(null);

  const canCreateRun =
    Boolean(datasetVersionId) &&
    Boolean(config) &&
    configurationValidated &&
    !disabled &&
    !loading;

  // --------------------------------------------------------------------------
  // Create Run
  // --------------------------------------------------------------------------

  const handleCreateRun = async () => {
    if (!canCreateRun) {
      return;
    }

    setLoading(true);
    setError("");
    setCreatedRun(null);

    try {
      const response = await createPreprocessingRun(
        datasetVersionId,
        config,
      );

      const run = normalizeRun(response);

      if (!run || typeof run !== "object") {
        throw new Error(
          "The server returned an invalid preprocessing run.",
        );
      }

      setCreatedRun(run);
      onRunCreated?.(run);
    } catch (requestError) {
      setError(formatError(requestError));
    } finally {
      setLoading(false);
    }
  };

  const runId = getRunId(createdRun);

  // --------------------------------------------------------------------------
  // Render
  // --------------------------------------------------------------------------

  return (
    <section
      className="preprocessing-panel preprocessing-pipeline-execution"
      aria-labelledby="preprocessing-execution-title"
    >
      <div className="preprocessing-panel-heading">
        <div className="preprocessing-heading-icon">
          <CirclePlay size={19} aria-hidden="true" />
        </div>

        <div className="preprocessing-heading-copy">
          <h2 id="preprocessing-execution-title">
            Pipeline Execution
          </h2>

          <p>Run the validated configuration on this dataset.</p>
        </div>
      </div>

      {/* Run Summary */}

      <div className="preprocessing-execution-summary">
        <div className="preprocessing-execution-summary-item">
          <span>Dataset version</span>
          <strong>
            {datasetVersionId || "Not selected"}
          </strong>
        </div>

        <div className="preprocessing-execution-summary-item">
          <span>Configuration validation</span>
          <strong>
            {configurationValidated
              ? "Passed"
              : "Not validated"}
          </strong>
        </div>
      </div>

      {/* Actions */}

      {canManage && <div className="preprocessing-execution-actions">
        <button
          type="button"
          className="preprocessing-primary-button"
          onClick={handleCreateRun}
          disabled={!canCreateRun}
        >
          {loading ? (
            <>
              <Loader2
                size={16}
                className="preprocessing-spinner"
                aria-hidden="true"
              />
              Creating run...
            </>
          ) : (
            <>
              <CirclePlay size={16} aria-hidden="true" />
              Create Preprocessing Run
            </>
          )}
        </button>

        {!datasetVersionId || !configurationValidated ? (
          <small>
            Select a dataset and validate its configuration to enable execution.
          </small>
        ) : null}
      </div>}

      {/* API Error */}

      {error && (
        <div
          className="preprocessing-validation-error"
          role="alert"
        >
          <AlertCircle size={17} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Created Run */}

      {createdRun && (
        <div
          className="preprocessing-validation-success"
          role="status"
        >
          <CheckCircle2 size={17} aria-hidden="true" />

          <div>
            <strong>Run created successfully.</strong>

            <p>
              Run ID:{" "}
              {runId ? (
                <code>{runId}</code>
              ) : (
                "Unavailable"
              )}
            </p>

            <p>
              Status: {createdRun.status ?? "Unavailable"}
            </p>

          </div>
        </div>
      )}
    </section>
  );
}

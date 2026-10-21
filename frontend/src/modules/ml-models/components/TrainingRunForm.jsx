
import { useState } from "react";

export default function TrainingRunForm({
  onSubmit,
  onCancel,
  submitting = false,
}) {
  const [modelId, setModelId] = useState("");
  const [preprocessingRunId, setPreprocessingRunId] = useState("");
  const [configText, setConfigText] = useState("{}");
  const [configError, setConfigError] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    setConfigError("");

    let configSnapshot;

    try {
      configSnapshot = JSON.parse(configText);
    } catch {
      setConfigError("Configuration must be valid JSON.");
      return;
    }

    if (
      !configSnapshot ||
      Array.isArray(configSnapshot) ||
      typeof configSnapshot !== "object"
    ) {
      setConfigError("Configuration must be a JSON object.");
      return;
    }

    onSubmit?.({
      model_definition_id: modelId.trim(),
      preprocessing_run_id: preprocessingRunId.trim(),
      config_snapshot: configSnapshot,
    });
  };

  return (
    <form className="ml-training-form" onSubmit={handleSubmit}>
      <div className="ml-training-form__header">
        <div>
          <h2>Create Training Run</h2>
          <p>
            Configure a model and preprocessing run to create a
            training job.
          </p>
        </div>
      </div>

      <div className="ml-training-form__body">
        <div className="ml-form-group">
          <label htmlFor="training-model-id">
            Model Definition ID <span>*</span>
          </label>
          <input
            id="training-model-id"
            type="text"
            value={modelId}
            onChange={(event) => setModelId(event.target.value)}
            placeholder="Enter model UUID"
            required
          />
          <small>
            Use the UUID of an existing model definition.
          </small>
        </div>

        <div className="ml-form-group">
          <label htmlFor="training-preprocessing-id">
            Preprocessing Run ID <span>*</span>
          </label>
          <input
            id="training-preprocessing-id"
            type="text"
            value={preprocessingRunId}
            onChange={(event) =>
              setPreprocessingRunId(event.target.value)
            }
            placeholder="Enter preprocessing run UUID"
            required
          />
          <small>
            Use the UUID of a completed preprocessing run.
          </small>
        </div>

        <div className="ml-form-group">
          <label htmlFor="training-config">
            Configuration Snapshot
          </label>
          <textarea
            id="training-config"
            value={configText}
            onChange={(event) => setConfigText(event.target.value)}
            rows={7}
            spellCheck={false}
            placeholder={'{\n  "random_state": 42\n}'}
          />
          <small>
            Enter a JSON object containing the training configuration.
          </small>
          {configError && (
            <p className="ml-form-error" role="alert">
              {configError}
            </p>
          )}
        </div>
      </div>

      <div className="ml-training-form__actions">
        <button
          type="button"
          className="ml-button ml-button--secondary"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="ml-button ml-button--primary"
          disabled={submitting}
        >
          {submitting ? "Creating..." : "Create Training Run"}
        </button>
      </div>
    </form>
  );
}
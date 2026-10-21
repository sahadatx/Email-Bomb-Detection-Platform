import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  X,
  GitBranch,
  Database,
  AlertCircle,
} from "lucide-react";

import DatasetSplitConfiguration from "./DatasetSplitConfiguration";

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

const DEFAULT_SPLIT = {
  training_percentage: 70,
  validation_percentage: 15,
  testing_percentage: 15,
  random_seed: 42,
  stratified: true,
};

const INITIAL_FORM_STATE = {
  datasetId: "",
  versionName: "",
  configuration: DEFAULT_SPLIT,
};

/* -------------------------------------------------------------------------- */
/* Dataset Helpers                                                            */
/* -------------------------------------------------------------------------- */

function getDatasetId(dataset) {
  return dataset?.dataset_id ?? dataset?.id ?? "";
}

function getDatasetName(dataset) {
  return (
    dataset?.name ??
    dataset?.dataset_name ??
    "Untitled Dataset"
  );
}

function getDatasetCount(dataset) {
  const value =
    dataset?.sample_count ??
    dataset?.email_count ??
    dataset?.total_emails;

  if (value === null || value === undefined || value === "") {
    return null;
  }

  const count = Number(value);

  return Number.isFinite(count) && count >= 0
    ? count
    : null;
}

/* -------------------------------------------------------------------------- */
/* Error Helpers                                                              */
/* -------------------------------------------------------------------------- */

function getErrorText(error) {
  if (!error) {
    return "";
  }

  if (typeof error === "string") {
    return error;
  }

  if (Array.isArray(error)) {
    return error
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        const location = Array.isArray(item?.loc)
          ? item.loc.join(".")
          : "";

        const message = item?.msg ?? item?.message ?? String(item);

        return location
          ? `${location}: ${message}`
          : message;
      })
      .join("; ");
  }

  const responseData = error?.response?.data;

  const detail =
    responseData?.detail ??
    responseData?.message ??
    responseData?.error?.message ??
    responseData?.error?.details ??
    error?.detail ??
    error?.message;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return getErrorText(detail);
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return "Unable to create dataset version.";
}

/* -------------------------------------------------------------------------- */
/* Split Helpers                                                              */
/* -------------------------------------------------------------------------- */

function toNumber(value) {
  if (
    value === "" ||
    value === null ||
    value === undefined
  ) {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function normalizeSplit(configuration = {}) {
  return {
    training_percentage:
      configuration.training_percentage ??
      configuration.train_percent ??
      configuration.train_percentage ??
      DEFAULT_SPLIT.training_percentage,

    validation_percentage:
      configuration.validation_percentage ??
      configuration.validation_percent ??
      configuration.val_percent ??
      DEFAULT_SPLIT.validation_percentage,

    testing_percentage:
      configuration.testing_percentage ??
      configuration.test_percent ??
      configuration.test_percentage ??
      DEFAULT_SPLIT.testing_percentage,

    random_seed:
      configuration.random_seed ??
      configuration.randomSeed ??
      DEFAULT_SPLIT.random_seed,

    stratified:
      typeof configuration.stratified === "boolean"
        ? configuration.stratified
        : DEFAULT_SPLIT.stratified,
  };
}

function validateSplit(configuration) {
  const split = normalizeSplit(configuration);

  const training = toNumber(split.training_percentage);
  const validation = toNumber(split.validation_percentage);
  const testing = toNumber(split.testing_percentage);
  const seed = toNumber(split.random_seed);

  const percentages = [
    training,
    validation,
    testing,
  ];

  if (percentages.some((value) => value === null)) {
    return {
      valid: false,
      total: null,
      message: "Enter all three split percentages.",
      split,
    };
  }

  if (
    percentages.some(
      (value) =>
        !Number.isInteger(value) ||
        value < 0 ||
        value > 100
    )
  ) {
    return {
      valid: false,
      total: percentages.reduce(
        (sum, value) => sum + (value ?? 0),
        0
      ),
      message:
        "Percentages must be whole numbers between 0 and 100.",
      split,
    };
  }

  const total = training + validation + testing;

  if (total !== 100) {
    return {
      valid: false,
      total,
      message:
        "Split percentages must total exactly 100%.",
      split,
    };
  }

  if (
    seed === null ||
    !Number.isInteger(seed) ||
    seed < 0
  ) {
    return {
      valid: false,
      total,
      message:
        "Random seed must be a non-negative integer.",
      split,
    };
  }

  if (typeof split.stratified !== "boolean") {
    return {
      valid: false,
      total,
      message: "Select a valid stratified setting.",
      split,
    };
  }

  return {
    valid: true,
    total,
    message: "",
    split: {
      ...split,
      training_percentage: training,
      validation_percentage: validation,
      testing_percentage: testing,
      random_seed: seed,
    },
  };
}

/* -------------------------------------------------------------------------- */
/* Payload Builder                                                            */
/* -------------------------------------------------------------------------- */

function buildCreatePayload({
  datasetId,
  versionName,
  configuration,
}) {
  const name = String(versionName ?? "").trim();

  if (!datasetId) {
    throw new Error("Please select a dataset.");
  }

  if (!name) {
    throw new Error("Version name is required.");
  }

  if (name.length > 255) {
    throw new Error(
      "Version name must not exceed 255 characters."
    );
  }

  const result = validateSplit(configuration);

  if (!result.valid) {
    throw new Error(result.message);
  }

  return {
    dataset_id: datasetId,
    name,
    split: {
      training_percentage:
        result.split.training_percentage,
      validation_percentage:
        result.split.validation_percentage,
      testing_percentage:
        result.split.testing_percentage,
      random_seed: result.split.random_seed,
      stratified: result.split.stratified,
    },
  };
}

/* -------------------------------------------------------------------------- */
/* Dataset Version Modal                                                      */
/* -------------------------------------------------------------------------- */

export default function DatasetVersionModal({
  open = false,
  datasets = [],
  initialDatasetId = "",
  submitting = false,
  error = null,
  onClose,
  onSubmit,
  className = "",
}) {
  /* ------------------------------------------------------------------------ */
  /* State                                                                    */
  /* ------------------------------------------------------------------------ */

  const [datasetId, setDatasetId] = useState("");
  const [versionName, setVersionName] = useState("");
  const [configuration, setConfiguration] = useState(
    () => ({ ...DEFAULT_SPLIT })
  );
  const [validationError, setValidationError] = useState("");

  /* ------------------------------------------------------------------------ */
  /* Reset Form                                                               */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (!open) {
      return;
    }

    const defaultDatasetId =
      initialDatasetId ||
      (datasets.length === 1
        ? getDatasetId(datasets[0])
        : "");

    setDatasetId(String(defaultDatasetId));
    setVersionName("");
    setConfiguration({ ...DEFAULT_SPLIT });
    setValidationError("");
  }, [open, initialDatasetId]);

  /* ------------------------------------------------------------------------ */
  /* Keyboard Handling                                                        */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !submitting) {
        event.preventDefault();
        onClose?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, submitting, onClose]);

  /* ------------------------------------------------------------------------ */
  /* Derived State                                                            */
  /* ------------------------------------------------------------------------ */

  const safeDatasets = Array.isArray(datasets)
    ? datasets
    : [];

  const selectedDataset = useMemo(
    () =>
      safeDatasets.find(
        (dataset) =>
          String(getDatasetId(dataset)) ===
          String(datasetId)
      ) ?? null,
    [safeDatasets, datasetId]
  );

  const splitValidation = useMemo(
    () => validateSplit(configuration),
    [configuration]
  );

  const externalError = getErrorText(error);

  const canSubmit =
    Boolean(datasetId) &&
    Boolean(versionName.trim()) &&
    versionName.trim().length <= 255 &&
    splitValidation.valid &&
    !submitting;

  /* ------------------------------------------------------------------------ */
  /* Form Handlers                                                            */
  /* ------------------------------------------------------------------------ */

  const handleDatasetChange = useCallback((event) => {
    setDatasetId(event.target.value);
    setValidationError("");
  }, []);

  const handleVersionNameChange = useCallback((event) => {
    setVersionName(event.target.value);
    setValidationError("");
  }, []);

  const handleConfigurationChange = useCallback(
    (nextConfiguration) => {
      setConfiguration(
        normalizeSplit(nextConfiguration)
      );
      setValidationError("");
    },
    []
  );

  /* ------------------------------------------------------------------------ */
  /* Submit                                                                    */
  /* ------------------------------------------------------------------------ */

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault();

      if (submitting) {
        return;
      }

      try {
        const payload = buildCreatePayload({
          datasetId,
          versionName,
          configuration,
        });

        setValidationError("");

        if (typeof onSubmit !== "function") {
          throw new Error(
            "Version submission is not configured."
          );
        }

        await onSubmit(payload);
      } catch (submitError) {
        setValidationError(getErrorText(submitError));
      }
    },
    [
      submitting,
      datasetId,
      versionName,
      configuration,
      onSubmit,
    ]
  );

  /* ------------------------------------------------------------------------ */
  /* Close Handlers                                                           */
  /* ------------------------------------------------------------------------ */

  const handleClose = useCallback(() => {
    if (!submitting) {
      onClose?.();
    }
  }, [submitting, onClose]);

  const handleBackdropMouseDown = useCallback(
    (event) => {
      if (
        event.target === event.currentTarget &&
        !submitting
      ) {
        onClose?.();
      }
    },
    [submitting, onClose]
  );

  /* ------------------------------------------------------------------------ */
  /* Render                                                                   */
  /* ------------------------------------------------------------------------ */

  if (!open) {
    return null;
  }

  const modalClassName = [
    "dataset-version-modal",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const backdropClassName = [
    "dataset-modal-backdrop",
    className.includes("dataset-version-modal--drawer")
      ? "dataset-modal-backdrop--drawer"
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={backdropClassName}
      onMouseDown={handleBackdropMouseDown}
    >
      <section
        className={modalClassName}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dataset-version-modal-title"
        aria-describedby="dataset-version-modal-description"
      >
        {/* Modal Header */}
        <header className="dataset-version-modal__header">
          <div className="dataset-version-modal__heading">
            <div className="dataset-version-modal__icon">
              <GitBranch size={21} />
            </div>

            <div>
              <h2 id="dataset-version-modal-title">
                Create Dataset Version
              </h2>

              <p id="dataset-version-modal-description">
                Create an immutable version with a reproducible
                training, validation, and testing split.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="dataset-icon-button"
            onClick={handleClose}
            disabled={submitting}
            aria-label="Close version modal"
            title="Close"
          >
            <X size={20} />
          </button>
        </header>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="dataset-version-modal__body">
            {/* Dataset Selector */}
            <div className="dataset-form-field">
              <label htmlFor="version-dataset">
                Dataset <span aria-hidden="true">*</span>
              </label>

              <select
                id="version-dataset"
                name="dataset_id"
                value={datasetId}
                onChange={handleDatasetChange}
                disabled={
                  submitting ||
                  Boolean(initialDatasetId)
                }
                required
              >
                <option value="">
                  Select a dataset
                </option>

                {safeDatasets.map((dataset) => {
                  const id = getDatasetId(dataset);

                  if (!id) {
                    return null;
                  }

                  return (
                    <option key={id} value={id}>
                      {getDatasetName(dataset)}
                    </option>
                  );
                })}
              </select>

              {safeDatasets.length === 0 && (
                <small>
                  No datasets are available. Create a dataset
                  in the Dataset Workspace first.
                </small>
              )}
            </div>

            {/* Selected Dataset Summary */}
            {selectedDataset && (
              <div className="dataset-version-modal__dataset-summary">
                <Database size={18} />

                <div>
                  <strong>
                    {getDatasetName(selectedDataset)}
                  </strong>

                  <span>
                    {getDatasetCount(selectedDataset) === null
                      ? "Sample count unavailable"
                      : `${getDatasetCount(
                          selectedDataset
                        ).toLocaleString()} samples`}
                  </span>
                </div>
              </div>
            )}

            {/* Version Name */}
            <div className="dataset-form-field">
              <label htmlFor="dataset-version-name">
                Version Name <span aria-hidden="true">*</span>
              </label>

              <input
                id="dataset-version-name"
                name="name"
                type="text"
                value={versionName}
                onChange={handleVersionNameChange}
                placeholder="e.g. Initial Training Dataset"
                maxLength={255}
                required
                disabled={submitting}
                aria-invalid={
                  versionName.trim().length > 255
                }
              />

              <small>
                Enter a descriptive name for this immutable
                dataset version. Maximum 255 characters.
              </small>
            </div>

            {/* Split Configuration */}
            <DatasetSplitConfiguration
              value={configuration}
              onChange={handleConfigurationChange}
              disabled={submitting}
            />

            {/* Split Validation Summary */}
            <div
              className={
                splitValidation.valid
                  ? "dataset-version-modal__split-status dataset-version-modal__split-status--valid"
                  : "dataset-version-modal__split-status dataset-version-modal__split-status--invalid"
              }
              aria-live="polite"
            >
              <span>
                Split total:{" "}
                {splitValidation.total === null
                  ? "—"
                  : `${splitValidation.total}%`}
              </span>

              <span>
                {splitValidation.valid
                  ? "Split percentages total 100%."
                  : splitValidation.message}
              </span>
            </div>

            {/* Errors */}
            {(validationError || externalError) && (
              <div
                className="dataset-form-error"
                role="alert"
              >
                <AlertCircle size={17} />

                <span>
                  {validationError || externalError}
                </span>
              </div>
            )}
          </div>

          {/* Modal Footer */}
          <footer className="dataset-version-modal__footer">
            <button
              type="button"
              className="dataset-button dataset-button--secondary"
              onClick={handleClose}
              disabled={submitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="dataset-button dataset-button--primary"
              disabled={!canSubmit}
            >
              {submitting ? (
                <>
                  <span className="dataset-spinner dataset-spinner--small" />
                  Creating...
                </>
              ) : (
                <>
                  <GitBranch size={16} />
                  Create Version
                </>
              )}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

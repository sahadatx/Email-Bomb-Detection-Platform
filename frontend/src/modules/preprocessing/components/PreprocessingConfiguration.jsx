
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  Loader2,
  RotateCcw,
  Settings2,
} from "lucide-react";

import {
  DEFAULT_PREPROCESSING_CONFIG,
  FEATURE_ORDER,
  FEATURE_LABELS,
  FEATURE_TYPES,
  MISSING_VALUE_STRATEGIES,
  SCALING_METHODS,
} from "../types";

import {
  validatePreprocessingConfig,
  getPreprocessingErrorMessage,
} from "../services/preprocessingService";

// ============================================================================
// CONFIGURATION OPTIONS
// ============================================================================

const MISSING_LABELS = {
  mean: "Mean",
  median: "Median",
  most_frequent: "Most frequent",
  constant: "Constant value",
  drop: "Drop rows",
};

const SCALING_LABELS = {
  none: "No scaling",
  standard: "Standard scaling",
  minmax: "Min-Max scaling",
};

const DEFAULT_MISSING_OPTIONS = [
  "mean",
  "median",
  "most_frequent",
  "constant",
  "drop",
];

const DEFAULT_SCALING_OPTIONS = [
  "none",
  "standard",
  "minmax",
];

const SCALABLE_FEATURES = FEATURE_ORDER.filter(
  (feature) => FEATURE_TYPES?.[feature] !== "string",
);

// ============================================================================
// HELPERS
// ============================================================================

function normalizeOptions(source, fallback) {
  if (Array.isArray(source)) {
    const options = source
      .map((item) => {
        if (typeof item === "string") return item;
        if (typeof item?.value === "string") return item.value;
        if (typeof item?.name === "string") return item.name;
        return null;
      })
      .filter(Boolean);

    return options.length ? [...new Set(options)] : [...fallback];
  }

  if (source && typeof source === "object") {
    const values = Object.values(source).filter(
      (value) => typeof value === "string",
    );

    const options = values.length ? values : Object.keys(source);

    return options.length ? [...new Set(options)] : [...fallback];
  }

  return [...fallback];
}

/**
 * Convert the UI configuration into the exact configuration
 * contract expected by the backend.
 */
function getInitialConfig(value) {
  const defaults = DEFAULT_PREPROCESSING_CONFIG ?? {};
  const source = value ?? {};

  const featureOrder = Array.isArray(source.feature_order)
    ? source.feature_order.filter((feature) =>
        FEATURE_ORDER.includes(feature),
      )
    : Array.isArray(defaults.feature_order)
      ? defaults.feature_order.filter((feature) =>
          FEATURE_ORDER.includes(feature),
        )
      : [...FEATURE_ORDER];

  const missingStrategy =
    source.missing_value_strategy ??
    defaults.missing_value_strategy ??
    "median";

  // Support old UI naming when loading a saved configuration.
  const scalingStrategy =
    source.scaling_strategy ??
    source.scaling_method ??
    defaults.scaling_strategy ??
    defaults.scaling_method ??
    "standard";

  const duplicateCheck =
    source.check_duplicates ??
    source.duplicate_check ??
    defaults.check_duplicates ??
    defaults.duplicate_check ??
    true;

  const suppliedScalingFeatures = Array.isArray(
    source.scaling_features,
  )
    ? source.scaling_features
    : Array.isArray(defaults.scaling_features)
      ? defaults.scaling_features
      : null;

  const scalingFeatures =
    scalingStrategy === "none"
      ? []
      : suppliedScalingFeatures === null
        ? SCALABLE_FEATURES.filter((feature) =>
            featureOrder.includes(feature),
          )
        : suppliedScalingFeatures.filter(
            (feature) =>
              SCALABLE_FEATURES.includes(feature) &&
              featureOrder.includes(feature),
          );

  // Do not send UI-only or legacy keys to the backend.
  return {
    feature_order: [...new Set(featureOrder)],
    missing_value_strategy: missingStrategy,
    missing_value_constant:
      missingStrategy === "constant"
        ? source.missing_value_constant ??
          defaults.missing_value_constant ??
          null
        : null,
    scaling_strategy: scalingStrategy,
    scaling_features: [...new Set(scalingFeatures)],
    check_duplicates: Boolean(duplicateCheck),
  };
}

function getValidationErrors(result) {
  if (Array.isArray(result?.errors)) {
    return result.errors;
  }

  if (Array.isArray(result?.detail)) {
    return result.detail;
  }

  if (result?.detail && typeof result.detail === "object") {
    return [result.detail];
  }

  if (typeof result?.detail === "string") {
    return [result.detail];
  }

  return [];
}

function formatValidationError(error) {
  if (typeof error === "string") return error;
  if (typeof error?.message === "string") return error.message;
  if (typeof error?.msg === "string") return error.msg;

  if (error && typeof error === "object") {
    const location = Array.isArray(error.loc)
      ? `${error.loc.join(" → ")}: `
      : "";

    const message = error.msg ?? error.message;

    if (typeof message === "string") {
      return `${location}${message}`;
    }
  }

  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

function getOptionLabel(value, labels) {
  return labels[value] ?? value;
}

function getErrorDetails(error) {
  const data = error?.response?.data;
  const detail = data?.detail;

  if (Array.isArray(detail)) {
    return detail;
  }

  if (detail && typeof detail === "object") {
    if (Array.isArray(detail.errors)) return detail.errors;
    return [detail];
  }

  return [];
}

// ============================================================================
// FEATURE OPTION
// ============================================================================

function FeatureOption({ feature, checked, disabled, onChange }) {
  return (
    <label
      className={`preprocessing-feature-option ${
        checked ? "is-selected" : ""
      }`}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={onChange}
      />

      <span className="preprocessing-feature-checkbox">
        {checked && (
          <CheckCircle2 size={15} aria-hidden="true" />
        )}
      </span>

      <span className="preprocessing-feature-copy">
        <strong>{feature}</strong>
        <small>{FEATURE_LABELS?.[feature] ?? feature}</small>
      </span>
    </label>
  );
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function PreprocessingConfiguration({
  value,
  onChange,
  disabled = false,
  datasetVersionId = "",
  onValidationChange,
  readOnly = false,
}) {
  const [config, setConfig] = useState(() =>
    getInitialConfig(value),
  );

  const [validationState, setValidationState] = useState("idle");
  const [validationMessage, setValidationMessage] = useState("");
  const [validationErrors, setValidationErrors] = useState([]);
  const [validating, setValidating] = useState(false);

  const missingOptions = useMemo(
    () =>
      normalizeOptions(
        MISSING_VALUE_STRATEGIES,
        DEFAULT_MISSING_OPTIONS,
      ),
    [],
  );

  const scalingOptions = useMemo(
    () =>
      normalizeOptions(
        SCALING_METHODS,
        DEFAULT_SCALING_OPTIONS,
      ),
    [],
  );

  const selectedFeatures = useMemo(
    () => new Set(config.feature_order),
    [config.feature_order],
  );

  const missingStrategy = config.missing_value_strategy;
  const scalingStrategy = config.scaling_strategy;

  const showConstant = missingStrategy === "constant";
  const showScalingFeatures = scalingStrategy !== "none";

  // --------------------------------------------------------------------------
  // Synchronize Parent Configuration
  // --------------------------------------------------------------------------

  useEffect(() => {
    if (value === undefined || value === null) return;

    setConfig(getInitialConfig(value));
    setValidationState("idle");
    setValidationMessage("");
    setValidationErrors([]);
  }, [value]);

  // --------------------------------------------------------------------------
  // Validation State
  // --------------------------------------------------------------------------

  const clearValidation = useCallback(() => {
    setValidationState("idle");
    setValidationMessage("");
    setValidationErrors([]);
    onValidationChange?.(null);
  }, [onValidationChange]);

  // --------------------------------------------------------------------------
  // Configuration Updates
  // --------------------------------------------------------------------------

  const updateConfig = useCallback(
    (updates) => {
      setConfig((previous) => {
        const next = {
          ...previous,
          ...updates,
        };

        // Keep the backend contract consistent.
        if (next.scaling_strategy === "none") {
          next.scaling_features = [];
        }

        onChange?.(next);
        return next;
      });

      clearValidation();
    },
    [onChange, clearValidation],
  );

  const toggleFeature = (feature) => {
    if (disabled) return;

    const isSelected = selectedFeatures.has(feature);

    const nextFeatures = isSelected
      ? config.feature_order.filter((item) => item !== feature)
      : FEATURE_ORDER.filter(
          (item) =>
            item === feature || selectedFeatures.has(item),
        );

    const nextScalingFeatures =
      config.scaling_strategy === "none"
        ? []
        : config.scaling_features.filter((item) =>
            nextFeatures.includes(item),
          );

    updateConfig({
      feature_order: nextFeatures,
      scaling_features: nextScalingFeatures,
    });
  };

  const toggleScalingFeature = (feature) => {
    if (
      disabled ||
      !selectedFeatures.has(feature) ||
      !SCALABLE_FEATURES.includes(feature) ||
      config.scaling_strategy === "none"
    ) {
      return;
    }

    const isSelected = config.scaling_features.includes(feature);

    const nextScalingFeatures = isSelected
      ? config.scaling_features.filter(
          (item) => item !== feature,
        )
      : SCALABLE_FEATURES.filter(
          (item) =>
            item === feature ||
            config.scaling_features.includes(item),
        );

    updateConfig({
      scaling_features: nextScalingFeatures,
    });
  };

  const resetConfiguration = () => {
    if (disabled) return;

    const nextConfig = getInitialConfig();

    setConfig(nextConfig);
    clearValidation();
    onChange?.(nextConfig);
  };

  // --------------------------------------------------------------------------
  // Backend Validation
  // --------------------------------------------------------------------------

  const handleValidate = async () => {
    if (disabled || validating || !datasetVersionId) return;

    setValidating(true);
    setValidationState("loading");
    setValidationMessage("");
    setValidationErrors([]);
    onValidationChange?.(null);

    try {
      // Send only fields defined by PreprocessingConfigRequest.
      const payload = getInitialConfig(config);

      const result = await validatePreprocessingConfig(payload);
      const errors = getValidationErrors(result);

      if (result?.valid !== true || errors.length > 0) {
        const message =
          result?.message ??
          (typeof result?.detail === "string"
            ? result.detail
            : "Please correct the configuration errors.");

        setValidationState("invalid");
        setValidationMessage(message);
        setValidationErrors(errors);

        onValidationChange?.({
          ...result,
          valid: false,
        });

        return;
      }

      setValidationState("valid");
      setValidationMessage(
        result?.message ?? "Configuration validation passed.",
      );

      onValidationChange?.({
        ...result,
        valid: true,
      });
    } catch (error) {
      const message = getPreprocessingErrorMessage(error);
      const details = getErrorDetails(error);

      setValidationState("invalid");
      setValidationMessage(message);
      setValidationErrors(details);

      onValidationChange?.({
        valid: false,
        error: message,
        details,
      });
    } finally {
      setValidating(false);
    }
  };

  // --------------------------------------------------------------------------
  // Render
  // --------------------------------------------------------------------------

  return (
    <section
      className="preprocessing-panel preprocessing-configuration"
      aria-labelledby="preprocessing-configuration-title"
    >
      <div className="preprocessing-panel-heading">
        <div className="preprocessing-heading-icon">
          <Settings2 size={19} aria-hidden="true" />
        </div>

        <div className="preprocessing-heading-copy">
          <h2 id="preprocessing-configuration-title">
            Preprocessing Configuration
          </h2>
          <p>
            Configure feature selection and dataset
            transformations.
          </p>
        </div>
      </div>

      {/* Feature Selection */}

      <div className="preprocessing-config-section">
        <div className="preprocessing-config-section-heading">
          <div>
            <h3>Feature Selection</h3>
            <p>
              Select the features to include in preprocessing.
            </p>
          </div>

          <span className="preprocessing-config-count">
            {config.feature_order.length} / {FEATURE_ORDER.length}
          </span>
        </div>

        <div className="preprocessing-feature-grid">
          {FEATURE_ORDER.map((feature) => (
            <FeatureOption
              key={feature}
              feature={feature}
              checked={selectedFeatures.has(feature)}
              disabled={disabled}
              onChange={() => toggleFeature(feature)}
            />
          ))}
        </div>
      </div>

      {/* Missing Value Handling */}

      <div className="preprocessing-config-section">
        <div className="preprocessing-config-section-heading">
          <div>
            <h3>Missing Value Handling</h3>
            <p>
              Choose how missing feature values should be handled.
            </p>
          </div>
        </div>

        <div className="preprocessing-form-field">
          <label htmlFor="preprocessing-missing-strategy">
            Missing value strategy
          </label>

          <select
            id="preprocessing-missing-strategy"
            value={missingStrategy}
            disabled={disabled}
            onChange={(event) => {
              const strategy = event.target.value;

              updateConfig({
                missing_value_strategy: strategy,
                missing_value_constant:
                  strategy === "constant"
                    ? config.missing_value_constant
                    : null,
              });
            }}
          >
            {missingOptions.map((strategy) => (
              <option key={strategy} value={strategy}>
                {getOptionLabel(strategy, MISSING_LABELS)}
              </option>
            ))}
          </select>
        </div>

        {showConstant && (
          <div className="preprocessing-form-field">
            <label htmlFor="preprocessing-missing-constant">
              Constant value
            </label>

            <input
              id="preprocessing-missing-constant"
              type="number"
              value={config.missing_value_constant ?? ""}
              disabled={disabled}
              onChange={(event) =>
                updateConfig({
                  missing_value_constant:
                    event.target.value === ""
                      ? null
                      : Number(event.target.value),
                })
              }
              placeholder="Enter a numeric constant"
            />

            <small>
              A value is required when the constant strategy is selected.
            </small>
          </div>
        )}

        {(missingStrategy === "mean" ||
          missingStrategy === "median") && (
          <div className="preprocessing-info-notice">
            <AlertCircle size={16} aria-hidden="true" />
            <span>
              Mean and median imputation are intended for numeric
              features. The backend validates the configuration.
            </span>
          </div>
        )}
      </div>

      {/* Feature Scaling */}

      <div className="preprocessing-config-section">
        <div className="preprocessing-config-section-heading">
          <div>
            <h3>Feature Scaling</h3>
            <p>
              Choose a scaling method and numeric features to scale.
            </p>
          </div>
        </div>

        <div className="preprocessing-form-field">
          <label htmlFor="preprocessing-scaling-method">
            Scaling method
          </label>

          <select
            id="preprocessing-scaling-method"
            value={scalingStrategy}
            disabled={disabled}
            onChange={(event) => {
              const strategy = event.target.value;

              updateConfig({
                scaling_strategy: strategy,
                scaling_features:
                  strategy === "none"
                    ? []
                    : SCALABLE_FEATURES.filter(
                        (feature) =>
                          selectedFeatures.has(feature),
                      ),
              });
            }}
          >
            {scalingOptions.map((method) => (
              <option key={method} value={method}>
                {getOptionLabel(method, SCALING_LABELS)}
              </option>
            ))}
          </select>
        </div>

        {showScalingFeatures && (
          <div className="preprocessing-scaling-features">
            <span className="preprocessing-field-label">
              Features to scale
            </span>

            <div className="preprocessing-scaling-grid">
              {SCALABLE_FEATURES.map((feature) => {
                const checked =
                  config.scaling_features.includes(feature);

                const selected =
                  selectedFeatures.has(feature);

                return (
                  <label
                    className="preprocessing-scaling-option"
                    key={feature}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={disabled || !selected}
                      onChange={() =>
                        toggleScalingFeature(feature)
                      }
                    />
                    <span>{feature}</span>
                  </label>
                );
              })}
            </div>

            <small>
              F1 is a string feature and cannot be scaled directly.
              Only selected numeric features can be scaled.
            </small>
          </div>
        )}

        {!showScalingFeatures && (
          <div className="preprocessing-info-notice">
            <AlertCircle size={16} aria-hidden="true" />
            <span>
              No scaling is selected. The scaling feature list will
              be sent as an empty array.
            </span>
          </div>
        )}
      </div>

      {/* Data Quality */}

      <div className="preprocessing-config-section">
        <div className="preprocessing-config-section-heading">
          <div>
            <h3>Data Quality</h3>
            <p>Configure duplicate-row checking.</p>
          </div>
        </div>

        <label className="preprocessing-toggle-option">
          <input
            type="checkbox"
            checked={config.check_duplicates}
            disabled={disabled}
            onChange={(event) =>
              updateConfig({
                check_duplicates: event.target.checked,
              })
            }
          />

          <span>
            <strong>Check for duplicate records</strong>
            <small>
              Enable duplicate detection during preprocessing.
            </small>
          </span>
        </label>
      </div>

      {/* Configuration Actions */}

      {!readOnly && <div className="preprocessing-config-actions">
        <button
          type="button"
          className="preprocessing-secondary-button"
          disabled={disabled || validating}
          onClick={resetConfiguration}
        >
          <RotateCcw size={15} aria-hidden="true" />
          Reset Configuration
        </button>

        <button
          type="button"
          className="preprocessing-primary-button"
          disabled={
            disabled ||
            validating ||
            !datasetVersionId
          }
          onClick={handleValidate}
        >
          {validating ? (
            <>
              <Loader2
                size={16}
                className="preprocessing-spinner"
                aria-hidden="true"
              />
              Validating...
            </>
          ) : (
            <>
              <ClipboardCheck size={16} aria-hidden="true" />
              Validate Configuration
            </>
          )}
        </button>
      </div>}

      {/* Validation Feedback */}

      {validationState === "loading" && (
        <div className="preprocessing-info-notice" role="status">
          <Loader2
            size={16}
            className="preprocessing-spinner"
            aria-hidden="true"
          />
          <span>Validating configuration...</span>
        </div>
      )}

      {validationState === "valid" && (
        <div
          className="preprocessing-validation-success"
          role="status"
        >
          <CheckCircle2 size={17} aria-hidden="true" />
          <span>{validationMessage}</span>
        </div>
      )}

      {validationState === "invalid" && (
        <div
          className="preprocessing-validation-error"
          role="alert"
        >
          <AlertCircle size={17} aria-hidden="true" />

          <div>
            <strong>{validationMessage}</strong>

            {validationErrors.length > 0 && (
              <ul>
                {validationErrors.map((error, index) => (
                  <li
                    key={`${index}-${formatValidationError(error)}`}
                  >
                    {formatValidationError(error)}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

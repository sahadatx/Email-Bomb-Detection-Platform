
/**
 * Module 06 — Preprocessing Pipeline
 *
 * API service for:
 * - Preprocessing configuration validation
 * - Validated dataset selection
 * - Preprocessing run creation
 * - Preprocessing run history
 * - Preprocessing run details
 * - Preprocessing artifacts
 * - API error handling
 *
 * Uses the shared API client.
 */

import apiClient from "../../../core/api/client";

import {
  PREPROCESSING_PAGINATION,
  PREPROCESSING_STATUS,
} from "../types";

// ============================================================================
// API CONFIGURATION
// ============================================================================

const API_PREFIX = "/preprocessing";

const MISSING_VALUE_STRATEGIES = new Set([
  "mean",
  "median",
  "most_frequent",
  "constant",
  "drop",
]);

const SCALING_STRATEGIES = new Set([
  "none",
  "standard",
  "minmax",
]);

const ALLOWED_FEATURES = new Set(
  Array.from({ length: 12 }, (_, index) => `F${index + 1}`)
);

const NUMERIC_FEATURES = new Set(
  Array.from({ length: 11 }, (_, index) => `F${index + 2}`)
);

// ============================================================================
// NORMALIZATION HELPERS
// ============================================================================

function normalizeId(value, fieldName = "id") {
  if (value === null || value === undefined) {
    throw new Error(`${fieldName} is required.`);
  }

  const normalized = String(value).trim();

  if (!normalized) {
    throw new Error(`${fieldName} is required.`);
  }

  return normalized;
}

function normalizePage(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return PREPROCESSING_PAGINATION.PAGE;
  }

  return Math.max(1, Math.trunc(number));
}

function normalizePageSize(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return PREPROCESSING_PAGINATION.PAGE_SIZE;
  }

  return Math.min(100, Math.max(1, Math.trunc(number)));
}

function normalizeOptionalString(value) {
  if (value === null || value === undefined) {
    return "";
  }

  return String(value).trim();
}

function validateObject(value, fieldName) {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value)
  ) {
    throw new TypeError(`${fieldName} must be an object.`);
  }
}

function normalizeSignalOptions(options = {}) {
  if (
    !options ||
    typeof options !== "object" ||
    Array.isArray(options)
  ) {
    throw new TypeError("Request options must be an object.");
  }

  return {
    signal: options.signal,
  };
}

// ============================================================================
// CONFIGURATION NORMALIZATION
// ============================================================================

/**
 * Convert frontend configuration fields to the backend schema.
 *
 * Frontend aliases:
 * - scaling_method -> scaling_strategy
 * - duplicate_check -> check_duplicates
 *
 * Backend fields:
 * - feature_order
 * - missing_value_strategy
 * - missing_value_constant
 * - scaling_strategy
 * - scaling_features
 * - check_duplicates
 */
export function normalizePreprocessingConfig(config) {
  validateObject(config, "Preprocessing configuration");

  const featureOrder = config.feature_order ?? [];
  const missingStrategy =
    config.missing_value_strategy ?? "median";

  const scalingStrategy =
    config.scaling_strategy ??
    config.scaling_method ??
    "standard";

  const scalingFeatures =
    config.scaling_features ?? null;

  const checkDuplicates =
    config.check_duplicates ??
    config.duplicate_check ??
    true;

  if (!Array.isArray(featureOrder)) {
    throw new TypeError("feature_order must be an array.");
  }

  if (
    !MISSING_VALUE_STRATEGIES.has(missingStrategy)
  ) {
    throw new Error(
      `Unsupported missing_value_strategy: ${missingStrategy}`
    );
  }

  if (!SCALING_STRATEGIES.has(scalingStrategy)) {
    throw new Error(
      `Unsupported scaling_strategy: ${scalingStrategy}`
    );
  }

  if (
    scalingFeatures !== null &&
    !Array.isArray(scalingFeatures)
  ) {
    throw new TypeError("scaling_features must be an array or null.");
  }

  if (typeof checkDuplicates !== "boolean") {
    throw new TypeError("check_duplicates must be a boolean.");
  }

  const normalizedFeatures = [...featureOrder];

  if (normalizedFeatures.length === 0) {
    throw new Error("At least one feature must be selected.");
  }

  if (
    normalizedFeatures.some(
      (feature) => typeof feature !== "string"
    )
  ) {
    throw new TypeError(
      "Every feature name must be a string."
    );
  }

  if (
    normalizedFeatures.some(
      (feature) => !ALLOWED_FEATURES.has(feature)
    )
  ) {
    throw new Error(
      "feature_order contains an unsupported feature."
    );
  }

  if (
    new Set(normalizedFeatures).size !==
    normalizedFeatures.length
  ) {
    throw new Error(
      "feature_order must not contain duplicate features."
    );
  }

  const canonicalOrder = [...normalizedFeatures].sort(
    (a, b) => Number(a.slice(1)) - Number(b.slice(1))
  );

  if (
    normalizedFeatures.some(
      (feature, index) => feature !== canonicalOrder[index]
    )
  ) {
    throw new Error(
      "feature_order must follow canonical F1-F12 order."
    );
  }

  let normalizedScalingFeatures =
    scalingFeatures === null
      ? canonicalOrder.filter((feature) =>
          NUMERIC_FEATURES.has(feature)
        )
      : [...scalingFeatures];

  if (
    normalizedScalingFeatures.some(
      (feature) => typeof feature !== "string"
    )
  ) {
    throw new TypeError(
      "Every scaling feature must be a string."
    );
  }

  if (
    new Set(normalizedScalingFeatures).size !==
    normalizedScalingFeatures.length
  ) {
    throw new Error(
      "scaling_features must not contain duplicates."
    );
  }

  for (const feature of normalizedScalingFeatures) {
    if (!ALLOWED_FEATURES.has(feature)) {
      throw new Error(
        `Unsupported scaling feature: ${feature}`
      );
    }

    if (!normalizedFeatures.includes(feature)) {
      throw new Error(
        `${feature} is not included in feature_order.`
      );
    }

    if (!NUMERIC_FEATURES.has(feature)) {
      throw new Error(
        `${feature} cannot be scaled directly.`
      );
    }
  }

  if (
    scalingStrategy === "none" &&
    normalizedScalingFeatures.length > 0
  ) {
    throw new Error(
      "scaling_features must be empty when scaling_strategy is 'none'."
    );
  }

  if (
    missingStrategy === "constant" &&
    (
      config.missing_value_constant === null ||
      config.missing_value_constant === undefined
    )
  ) {
    throw new Error(
      "missing_value_constant is required when the constant strategy is selected."
    );
  }

  if (
    missingStrategy !== "constant" &&
    config.missing_value_constant !== null &&
    config.missing_value_constant !== undefined
  ) {
    throw new Error(
      "missing_value_constant is only allowed with the constant strategy."
    );
  }

  return {
    feature_order: normalizedFeatures,
    missing_value_strategy: missingStrategy,
    missing_value_constant:
      missingStrategy === "constant"
        ? config.missing_value_constant
        : null,
    scaling_strategy: scalingStrategy,
    scaling_features: normalizedScalingFeatures,
    check_duplicates: checkDuplicates,
  };
}

// ============================================================================
// CONFIGURATION VALIDATION
// ============================================================================

/**
 * Validate preprocessing configuration.
 *
 * Backend:
 * POST /preprocessing/config/validate
 *
 * @param {Object} config
 * @param {Object} options
 * @returns {Promise<Object>}
 */
export async function validatePreprocessingConfig(
  config,
  options = {},
) {
  const payload = normalizePreprocessingConfig(config);
  const requestOptions = normalizeSignalOptions(options);

  const response = await apiClient.post(
    `${API_PREFIX}/config/validate`,
    payload,
    requestOptions,
  );

  return response.data;
}

// ============================================================================
// DATASET VERSION SELECTION
// ============================================================================

/**
 * Retrieve a dataset version for preprocessing.
 *
 * Only validated dataset versions are accepted by the backend.
 *
 * Backend:
 * GET /preprocessing/datasets/{dataset_version_id}
 *
 * @param {string} datasetVersionId
 * @param {Object} options
 * @returns {Promise<Object>}
 */
export async function getDatasetSelection(
  datasetVersionId,
  options = {},
) {
  const id = normalizeId(
    datasetVersionId,
    "datasetVersionId",
  );

  const requestOptions = normalizeSignalOptions(options);

  const response = await apiClient.get(
    `${API_PREFIX}/datasets/${encodeURIComponent(id)}`,
    requestOptions,
  );

  return response.data;
}

// ============================================================================
// CREATE PREPROCESSING RUN
// ============================================================================

/**
 * Create a preprocessing run.
 *
 * Backend:
 * POST /preprocessing/runs
 *
 * The backend creates the run in pending state.
 *
 * @param {string} datasetVersionId
 * @param {Object} config
 * @param {Object} options
 * @returns {Promise<Object>}
 */
export async function createPreprocessingRun(
  datasetVersionId,
  config,
  options = {},
) {
  const id = normalizeId(
    datasetVersionId,
    "datasetVersionId",
  );

  const normalizedConfig =
    normalizePreprocessingConfig(config);

  const requestOptions = normalizeSignalOptions(options);

  const response = await apiClient.post(
    `${API_PREFIX}/runs`,
    {
      dataset_version_id: id,
      config: normalizedConfig,
    },
    requestOptions,
  );

  return response.data;
}

// ============================================================================
// LIST PREPROCESSING RUNS
// ============================================================================

/**
 * Retrieve preprocessing run history.
 *
 * Supported query parameters:
 * - page
 * - page_size
 * - dataset_version_id
 * - status
 *
 * Backend:
 * GET /preprocessing/runs
 *
 * @param {Object} options
 * @param {number} options.page
 * @param {number} options.pageSize
 * @param {string} options.datasetVersionId
 * @param {string} options.status
 * @param {AbortSignal} options.signal
 * @returns {Promise<Object>}
 */
export async function getPreprocessingRuns({
  page = PREPROCESSING_PAGINATION.PAGE,
  pageSize = PREPROCESSING_PAGINATION.PAGE_SIZE,
  datasetId,
  datasetVersionId,
  status,
  signal,
} = {}) {
  const params = {
    page: normalizePage(page),
    page_size: normalizePageSize(pageSize),
  };

  const normalizedDatasetVersionId =
    normalizeOptionalString(datasetVersionId);

  const normalizedStatus =
    normalizeOptionalString(status);
  
  const normalizedDatasetId = normalizeOptionalString(datasetId);

  if (normalizedDatasetVersionId) {
    params.dataset_version_id =
      normalizedDatasetVersionId;
  }

  if (normalizedDatasetId) {
    params.dataset_id = normalizedDatasetId;
  }

  if (normalizedStatus && normalizedStatus !== "all") {
    const supportedStatuses =
      Object.values(PREPROCESSING_STATUS);

    if (!supportedStatuses.includes(normalizedStatus)) {
      throw new Error(
        `Unsupported preprocessing status: ${normalizedStatus}`,
      );
    }

    params.status = normalizedStatus;
  }

  const response = await apiClient.get(
    `${API_PREFIX}/runs`,
    {
      params,
      signal,
    },
  );

  return response.data;
}

// ============================================================================
// GET SINGLE PREPROCESSING RUN
// ============================================================================

/**
 * Retrieve a preprocessing run by ID.
 *
 * Backend:
 * GET /preprocessing/runs/{run_id}
 *
 * @param {string} runId
 * @param {Object} options
 * @returns {Promise<Object>}
 */
export async function getPreprocessingRun(
  runId,
  options = {},
) {
  const id = normalizeId(runId, "runId");
  const requestOptions = normalizeSignalOptions(options);

  const response = await apiClient.get(
    `${API_PREFIX}/runs/${encodeURIComponent(id)}`,
    requestOptions,
  );

  return response.data;
}

// ============================================================================
// GET PREPROCESSING RUN ARTIFACTS
// ============================================================================

/**
 * Retrieve artifacts belonging to a preprocessing run.
 *
 * Backend:
 * GET /preprocessing/runs/{run_id}/artifacts
 *
 * @param {string} runId
 * @param {Object} options
 * @returns {Promise<Object>}
 */
export async function getPreprocessingArtifacts(
  runId,
  options = {},
) {
  const id = normalizeId(runId, "runId");
  const requestOptions = normalizeSignalOptions(options);

  const response = await apiClient.get(
    `${API_PREFIX}/runs/${encodeURIComponent(id)}/artifacts`,
    requestOptions,
  );

  return response.data;
}

// ============================================================================
// EXECUTE PREPROCESSING RUN
// ============================================================================

/**
 * Queue a pending run for execution.
 *
 * Backend:
 * POST /preprocessing/runs/{run_id}/execute
 */
export async function executePreprocessingRun(
  runId,
  options = {},
) {
  const id = normalizeId(runId, "runId");
  const requestOptions = normalizeSignalOptions(options);

  const response = await apiClient.post(
    `${API_PREFIX}/runs/${encodeURIComponent(id)}/execute`,
    null,
    requestOptions,
  );

  return response.data;
}

// ============================================================================
// RUN NORMALIZATION
// ============================================================================

/**
 * Add the field names the UI components read, derived from the
 * backend run fields. Counts are hidden for runs without results.
 */
export function normalizeRun(run) {
  if (!run || typeof run !== "object") {
    return run;
  }

  const hasResults = run.status === "completed";

  const durationMs =
    run.duration_ms === null || run.duration_ms === undefined
      ? null
      : Number(run.duration_ms);

  const durationSeconds =
    durationMs !== null && Number.isFinite(durationMs)
      ? durationMs / 1000
      : null;

  return {
    ...run,
    input_count:
      run.input_count ??
      (hasResults ? run.input_sample_count : null),
    sample_count:
      run.sample_count ??
      (hasResults ? run.input_sample_count : null),
    output_count:
      run.output_count ??
      (hasResults ? run.output_sample_count : null),
    duration_seconds: run.duration_seconds ?? durationSeconds,
  };
}


export async function getPreprocessingSummary({
  datasetId,
  datasetVersionId,
  signal,
} = {}) {
  const params = {};

  const dsId = normalizeOptionalString(datasetId);
  const versionId = normalizeOptionalString(datasetVersionId);

  if (dsId) params.dataset_id = dsId;
  if (versionId) params.dataset_version_id = versionId;

  const response = await apiClient.get(`${API_PREFIX}/summary`, {
    params,
    signal,
  });

  return response.data;
}

export async function getPreprocessingFilters({ signal } = {}) {
  const response = await apiClient.get(`${API_PREFIX}/filters`, {
    signal,
  });

  return response.data;
}


// ============================================================================
// ERROR HANDLING
// ============================================================================

/**
 * Extract a readable message from an API error.
 *
 * The original error remains available to the caller.
 *
 * @param {Error|Object|null} error
 * @returns {string}
 */
export function getPreprocessingErrorMessage(error) {
  if (!error) {
    return "An unknown preprocessing error occurred.";
  }

  const data = error.response?.data;

  if (typeof data === "string" && data.trim()) {
    return data.trim();
  }

  if (data && typeof data === "object") {
    if (
      typeof data.message === "string" &&
      data.message.trim()
    ) {
      return data.message.trim();
    }

    if (
      typeof data.detail === "string" &&
      data.detail.trim()
    ) {
      return data.detail.trim();
    }

    if (
      data.detail &&
      typeof data.detail === "object" &&
      !Array.isArray(data.detail)
    ) {
      if (
        typeof data.detail.message === "string" &&
        data.detail.message.trim()
      ) {
        return data.detail.message.trim();
      }

      if (
        typeof data.detail.code === "string" &&
        data.detail.code.trim()
      ) {
        return data.detail.code.trim();
      }
    }

    if (Array.isArray(data.detail)) {
      const messages = data.detail
        .map((item) => {
          if (typeof item === "string") {
            return item;
          }

          if (typeof item?.msg === "string") {
            const location = Array.isArray(item.loc)
              ? item.loc.join(".")
              : "";

            return location
              ? `${location}: ${item.msg}`
              : item.msg;
          }

          return null;
        })
        .filter(Boolean);

      if (messages.length > 0) {
        return messages.join("; ");
      }
    }
  }

  if (
    typeof error.message === "string" &&
    error.message.trim()
  ) {
    return error.message.trim();
  }

  return (
    "An error occurred while communicating " +
    "with the preprocessing API."
  );
}

// ============================================================================
// SERVICE OBJECT
// ============================================================================

export const preprocessingService = Object.freeze({
  normalizePreprocessingConfig,
  validatePreprocessingConfig,
  getDatasetSelection,
  createPreprocessingRun,
  executePreprocessingRun,
  getPreprocessingRuns,
  getPreprocessingRun,
  getPreprocessingArtifacts,
  getPreprocessingErrorMessage,
  normalizeRun,
});

export default preprocessingService;

/**
 * Module 06 — Preprocessing Pipeline
 *
 * Shared constants and type definitions for the frontend.
 * Keep API response fields aligned with the backend schemas.
 */

// ============================================================================
// PREPROCESSING RUN STATUSES
// ============================================================================

export const PREPROCESSING_STATUS = Object.freeze({
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
});

export const PREPROCESSING_STATUS_LABELS = Object.freeze({
  [PREPROCESSING_STATUS.PENDING]: "Pending",
  [PREPROCESSING_STATUS.RUNNING]: "Running",
  [PREPROCESSING_STATUS.COMPLETED]: "Completed",
  [PREPROCESSING_STATUS.FAILED]: "Failed",
});

// ============================================================================
// DATASET SPLITS
// ============================================================================

export const DATASET_SPLITS = Object.freeze({
  TRAIN: "train",
  VALIDATION: "validation",
  TEST: "test",
});

// ============================================================================
// FEATURE DEFINITIONS
// ============================================================================

export const FEATURE_ORDER = Object.freeze([
  "F1",
  "F2",
  "F3",
  "F4",
  "F5",
  "F6",
  "F7",
  "F8",
  "F9",
  "F10",
  "F11",
  "F12",
]);

export const FEATURE_TYPES = Object.freeze({
  F1: "string",
  F2: "boolean",
  F3: "boolean",
  F4: "boolean",
  F5: "boolean",
  F6: "boolean",
  F7: "boolean",
  F8: "boolean",
  F9: "integer",
  F10: "integer",
  F11: "integer",
  F12: "integer",
});

export const FEATURE_LABELS = Object.freeze({
  F1: "Sender Email",
  F2: "Known Domain",
  F3: "Message ID",
  F4: "Auto Submitted",
  F5: "Precedence Bulk",
  F6: "List ID",
  F7: "X-BeenThere",
  F8: "X-Anti-Abuse",
  F9: "Keyword Features",
  F10: "Subject Length",
  F11: "Emails Per Minute",
  F12: "Emails Per Hour",
});

// ============================================================================
// MISSING-VALUE STRATEGIES
// ============================================================================

export const MISSING_VALUE_STRATEGIES = Object.freeze({
  MEAN: "mean",
  MEDIAN: "median",
  MOST_FREQUENT: "most_frequent",
  CONSTANT: "constant",
  DROP: "drop",
});

// ============================================================================
// SCALING METHODS
// ============================================================================

export const SCALING_METHODS = Object.freeze({
  NONE: "none",
  STANDARD: "standard",
  MINMAX: "minmax",
});

// ============================================================================
// DEFAULT PREPROCESSING CONFIGURATION
// ============================================================================

export const DEFAULT_PREPROCESSING_CONFIG = Object.freeze({
  feature_order: [...FEATURE_ORDER],

  missing_value_strategy: MISSING_VALUE_STRATEGIES.MEDIAN,

  missing_value_constant: null,

  scaling_method: SCALING_METHODS.STANDARD,

  scaling_features: FEATURE_ORDER.filter(
    (feature) => FEATURE_TYPES[feature] !== "string"
  ),

  duplicate_check: true,
});

// ============================================================================
// PREPROCESSING HISTORY PAGINATION
// ============================================================================

export const PREPROCESSING_PAGINATION = Object.freeze({
  PAGE: 1,
  PAGE_SIZE: 30,
});

// ============================================================================
// PREPROCESSING HISTORY FILTERS
// ============================================================================

export const PREPROCESSING_HISTORY_FILTERS = Object.freeze({
  ALL_STATUSES: "all",
  ALL_DATASETS: "all",
});

// ============================================================================
// PREPROCESSING RUN TYPE
// ============================================================================

/**
 * @typedef {Object} PreprocessingRun
 * @property {string} id
 * @property {string} dataset_version_id
 * @property {"pending"|"running"|"completed"|"failed"} status
 * @property {Object} config_snapshot
 * @property {Object|null} counts
 * @property {number|null} feature_count
 * @property {number|null} duration
 * @property {string|null} error_code
 * @property {string|null} error_message
 * @property {Object|null} result_summary
 * @property {string|null} created_at
 * @property {string|null} updated_at
 */

/**
 * @typedef {Object} PreprocessingConfiguration
 * @property {string[]} feature_order
 * @property {"mean"|"median"|"most_frequent"|"constant"|"drop"} missing_value_strategy
 * @property {number|string|null} missing_value_constant
 * @property {"none"|"standard"|"minmax"} scaling_method
 * @property {string[]} scaling_features
 * @property {boolean} duplicate_check
 */

/**
 * @typedef {Object} PreprocessingRunListResponse
 * @property {PreprocessingRun[]} items
 * @property {number} total
 */

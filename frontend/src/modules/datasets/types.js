
/**
 * Module 05 — Dataset Management
 *
 * Centralized frontend constants and data contracts.
 *
 * Responsibilities:
 * - Dataset Workspace
 * - Dataset Selection
 * - Dataset Management
 * - Dataset Versioning
 * - Train / Validation / Test Splitting
 * - Dataset Validation
 * - Dataset Export
 *
 * Architectural rules:
 * - F1–F12 are read from Module 04 canonical feature data.
 * - This module does not calculate or modify features.
 * - Dataset versions are immutable.
 * - Dataset membership belongs to a specific version.
 * - No prediction, risk score, or threat-level fields.
 */

// ============================================================================
// 1. MODULE CONFIGURATION
// ============================================================================

export const DATASET_MODULE = Object.freeze({
  NAME: "datasets",
  VERSION: "1.0.0",
  BASE_PATH: "/datasets",
  PAGE_SIZE: 30,
});

export const DATASET_ROUTES = Object.freeze({
  WORKSPACE: "/datasets",
  LIST: "/datasets/list",
  VERSIONS: "/datasets/versions",
  VALIDATION: "/datasets/validation",
  EXPORT: "/datasets/export",
});

// ============================================================================
// 2. DATASET CONSTANTS
// ============================================================================

export const DATASET_LABELS = Object.freeze({
  NORMAL: "normal",
  BOMBING: "bombing",
});

export const DATASET_SOURCES = Object.freeze({
  FILE_UPLOAD: "file_upload",
  RAW_EMAIL: "raw_email",
});

export const DATASET_SOURCE_LABELS = Object.freeze({
  [DATASET_SOURCES.FILE_UPLOAD]: "File Upload",
  [DATASET_SOURCES.RAW_EMAIL]: "Raw Email",
});

export const DATASET_STATUS = Object.freeze({
  ACTIVE: "active",
  ARCHIVED: "archived",
});

export const DATASET_STATUS_LABELS = Object.freeze({
  [DATASET_STATUS.ACTIVE]: "Active",
  [DATASET_STATUS.ARCHIVED]: "Archived",
});

// ============================================================================
// 3. CANONICAL FEATURE SCHEMA — MODULE 04
// ============================================================================

/**
 * Canonical F1–F12 feature definitions.
 *
 * These keys must match the actual Module 04 feature schema.
 * Dataset Management only displays and exports the existing values.
 *
 * Do not calculate feature values in this module.
 */
export const DATASET_FEATURES = Object.freeze([
  Object.freeze({
    code: "F1",
    key: "f1_sender_email",
    label: "Sender Email",
  }),
  Object.freeze({
    code: "F2",
    key: "f2_known_domain",
    label: "Known Domain",
  }),
  Object.freeze({
    code: "F3",
    key: "f3_message_id",
    label: "Message-ID",
  }),
  Object.freeze({
    code: "F4",
    key: "f4_auto_submitted",
    label: "Auto-Submitted",
  }),
  Object.freeze({
    code: "F5",
    key: "f5_precedence_bulk",
    label: "Precedence Bulk",
  }),
  Object.freeze({
    code: "F6",
    key: "f6_list_id",
    label: "List-Id",
  }),
  Object.freeze({
    code: "F7",
    key: "f7_x_beenthere",
    label: "X-BeenThere",
  }),
  Object.freeze({
    code: "F8",
    key: "f8_x_anti_abuse",
    label: "X-Anti-Abuse",
  }),
  Object.freeze({
    code: "F9",
    key: "f9_keyword_features",
    label: "Keyword Features",
  }),
  Object.freeze({
    code: "F10",
    key: "f10_subject_length",
    label: "Subject Length",
  }),
  Object.freeze({
    code: "F11",
    key: "f11_emails_per_minute",
    label: "Emails Per Minute",
  }),
  Object.freeze({
    code: "F12",
    key: "f12_emails_per_hour",
    label: "Emails Per Hour",
  }),
]);

export const DATASET_FEATURE_CODES = Object.freeze(
  DATASET_FEATURES.map(({ code }) => code)
);

export const DATASET_FEATURE_KEYS = Object.freeze(
  DATASET_FEATURES.map(({ key }) => key)
);

// ============================================================================
// 4. DATASET WORKSPACE
// ============================================================================

export const WORKSPACE_DEFAULT_FILTERS = Object.freeze({
  search: "",
  ground_truth: "",
  source: "",
  from_date: "",
  to_date: "",
});

export const WORKSPACE_SEARCH_FIELDS = Object.freeze([
  "subject",
  "sender",
  "message_id",
  "source_identifier",
]);

export const WORKSPACE_PAGE_SIZE = 30;

/**
 * @typedef {Object} DatasetWorkspaceFilters
 * @property {string} search
 * @property {string} ground_truth
 * @property {string} source
 * @property {string} from_date
 * @property {string} to_date
 */

/**
 * @typedef {Object} DatasetWorkspaceSummary
 * @property {number} total_emails
 * @property {number} normal_count
 * @property {number} bombing_count
 */

/**
 * @typedef {Object} DatasetEmail
 * @property {string} id
 * @property {string} [email_id]
 * @property {string} [subject]
 * @property {string} [sender]
 * @property {string} [message_id]
 * @property {string} [source_identifier]
 * @property {"normal"|"bombing"} ground_truth
 * @property {"file_upload"|"raw_email"} source
 * @property {string|null} [received_at]
 * @property {string|null} [collected_at]
 * @property {string|null} [parsed_at]
 * @property {Object<string, *>} [features]
 */

/**
 * @typedef {Object} DatasetWorkspaceResponse
 * @property {DatasetWorkspaceSummary} summary
 * @property {DatasetEmail[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} page_size
 * @property {number} total_pages
 */

// ============================================================================
// 5. DATASET SELECTION
// ============================================================================

export const DATASET_SELECTION_MODE = Object.freeze({
  MANUAL: "manual",
  ALL_MATCHING: "all_matching",
});

/**
 * @typedef {Object} DatasetSelection
 * @property {"manual"|"all_matching"} mode
 * @property {string[]} email_ids
 * @property {string[]} excluded_email_ids
 * @property {DatasetWorkspaceFilters} filters
 * @property {number} total_selected
 */

/**
 * @typedef {Object} DatasetSelectionSummary
 * @property {number} total_selected
 * @property {number} normal_count
 * @property {number} bombing_count
 */

// ============================================================================
// 6. DATASET
// ============================================================================

/**
 * @typedef {Object} DatasetSummary
 * @property {string} id
 * @property {string} name
 * @property {string|null} [description]
 * @property {number} sample_count
 * @property {number} normal_count
 * @property {number} bombing_count
 * @property {number} version_count
 * @property {string} created_at
 * @property {string} updated_at
 * @property {string} [status]
 */

/**
 * @typedef {DatasetSummary & {
 *   metadata?: Object<string, *>,
 *   feature_schema?: Array<{
 *     code: string,
 *     key: string,
 *     label: string
 *   }>
 * }} DatasetDetail
 */

/**
 * @typedef {Object} DatasetCreateRequest
 * @property {string} name
 * @property {string} [description]
 * @property {string[]} email_ids
 */

/**
 * @typedef {Object} DatasetListResponse
 * @property {DatasetSummary[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} page_size
 * @property {number} total_pages
 */

// ============================================================================
// 7. DATASET VERSIONING
// ============================================================================

export const DATASET_VERSION_STATUS = Object.freeze({
  CREATED: "created",
  VALIDATED: "validated",
  INVALID: "invalid",
});

export const DATASET_SPLIT_NAMES = Object.freeze({
  TRAIN: "train",
  VALIDATION: "validation",
  TEST: "test",
});

export const DEFAULT_SPLIT_CONFIGURATION = Object.freeze({
  train_percent: 70,
  validation_percent: 15,
  test_percent: 15,
  random_seed: 42,
  stratified: false,
});

/**
 * @typedef {Object} DatasetSplitConfiguration
 * @property {number} train_percent
 * @property {number} validation_percent
 * @property {number} test_percent
 * @property {number} random_seed
 * @property {boolean} stratified
 */

/**
 * @typedef {Object} DatasetVersionCreateRequest
 * @property {string} dataset_id
 * @property {string} [name]
 * @property {number} train_percent
 * @property {number} validation_percent
 * @property {number} test_percent
 * @property {number} random_seed
 * @property {boolean} stratified
 */

/**
 * @typedef {Object} DatasetVersionSummary
 * @property {string} id
 * @property {string} dataset_id
 * @property {string} [dataset_name]
 * @property {string} [name]
 * @property {number} sample_count
 * @property {number} train_count
 * @property {number} validation_count
 * @property {number} test_count
 * @property {DatasetSplitConfiguration} split_configuration
 * @property {string} created_at
 * @property {string} [status]
 */

/**
 * @typedef {DatasetVersionSummary & {
 *   metadata?: Object<string, *>,
 *   feature_schema?: Array<{
 *     code: string,
 *     key: string,
 *     label: string
 *   }>
 * }} DatasetVersionDetail
 */

/**
 * @typedef {Object} DatasetVersionListResponse
 * @property {DatasetVersionSummary[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} page_size
 * @property {number} total_pages
 */

// ============================================================================
// 8. DATASET MEMBERSHIP
// ============================================================================

/**
 * A membership records which email belongs to a specific immutable version
 * and which split it was assigned to.
 *
 * @typedef {Object} DatasetMembership
 * @property {string} id
 * @property {string} dataset_version_id
 * @property {string} email_id
 * @property {"train"|"validation"|"test"} split
 * @property {string} created_at
 */

// ============================================================================
// 9. SPLIT DISTRIBUTION
// ============================================================================

/**
 * @typedef {Object} DatasetSplitDistributionItem
 * @property {"train"|"validation"|"test"} split
 * @property {number} sample_count
 * @property {number} percentage
 */

/**
 * @typedef {Object} DatasetSplitDistribution
 * @property {DatasetSplitDistributionItem[]} items
 * @property {number} total_samples
 */

// ============================================================================
// 10. DATASET VALIDATION
// ============================================================================

export const DATASET_VALIDATION_STATUS = Object.freeze({
  VALID: "valid",
  INVALID: "invalid",
  WARNING: "warning",
});

export const DATASET_ISSUE_SEVERITY = Object.freeze({
  ERROR: "error",
  WARNING: "warning",
  INFO: "info",
});

export const DATASET_VALIDATION_CHECKS = Object.freeze([
  "feature_completeness",
  "ground_truth",
  "feature_schema",
  "duplicate_samples",
  "missing_samples",
  "invalid_feature_values",
  "split_integrity",
  "split_consistency",
  "membership_integrity",
]);

/**
 * @typedef {Object} DatasetValidationIssue
 * @property {string} code
 * @property {"error"|"warning"|"info"} severity
 * @property {string} message
 * @property {string} [description]
 * @property {number} [affected_samples]
 * @property {string[]} [email_ids]
 */

/**
 * @typedef {Object} DatasetValidationCheck
 * @property {string} code
 * @property {string} name
 * @property {"valid"|"invalid"|"warning"} status
 * @property {string} [message]
 * @property {number} [affected_samples]
 */

/**
 * @typedef {Object} DatasetValidationResponse
 * @property {string} dataset_id
 * @property {string} [version_id]
 * @property {"valid"|"invalid"|"warning"} status
 * @property {DatasetValidationCheck[]} checks
 * @property {DatasetValidationIssue[]} issues
 * @property {number} [total_samples]
 * @property {string} [validated_at]
 */

// ============================================================================
// 11. DATASET EXPORT
// ============================================================================

export const DATASET_EXPORT_FORMAT = Object.freeze({
  CSV: "csv",
  JSON: "json",
});

export const DATASET_EXPORT_SPLIT = Object.freeze({
  ALL: "all",
  TRAIN: "train",
  VALIDATION: "validation",
  TEST: "test",
});

/**
 * @typedef {Object} DatasetExportRequest
 * @property {string} version_id
 * @property {"csv"|"json"} format
 * @property {"all"|"train"|"validation"|"test"} split
 */

/**
 * @typedef {Object} DatasetExportPreview
 * @property {string[]} columns
 * @property {Array<Object<string, *>>} rows
 * @property {number} total_samples
 * @property {number} preview_limit
 * @property {"csv"|"json"} [format]
 * @property {string} [split]
 */

/**
 * @typedef {Object} DatasetExportResult
 * @property {string} [filename]
 * @property {string} [download_url]
 * @property {string} [content_type]
 * @property {number} [sample_count]
 * @property {"csv"|"json"} format
 * @property {"all"|"train"|"validation"|"test"} split
 */

// ============================================================================
// 12. API ERROR
// ============================================================================

/**
 * @typedef {Object} DatasetApiError
 * @property {string} message
 * @property {number} [status]
 * @property {string} [code]
 * @property {*} [details]
 */

// ============================================================================
// 13. DEFAULT VALUE FACTORIES
// ============================================================================

/**
 * Return a fresh copy of the default workspace filters.
 *
 * @returns {DatasetWorkspaceFilters}
 */
export function createDefaultDatasetFilters() {
  return { ...WORKSPACE_DEFAULT_FILTERS };
}

/**
 * Return a fresh split configuration.
 *
 * @returns {DatasetSplitConfiguration}
 */
export function createDefaultSplitConfiguration() {
  return { ...DEFAULT_SPLIT_CONFIGURATION };
}

/**
 * Return a fresh empty selection.
 *
 * @returns {DatasetSelection}
 */
export function createEmptyDatasetSelection() {
  return {
    mode: DATASET_SELECTION_MODE.MANUAL,
    email_ids: [],
    excluded_email_ids: [],
    filters: createDefaultDatasetFilters(),
    total_selected: 0,
  };
}

// ============================================================================
// 14. SPLIT HELPERS
// ============================================================================

/**
 * Calculate the total split percentage.
 *
 * @param {Partial<DatasetSplitConfiguration>} configuration
 * @returns {number}
 */
export function getSplitTotal(configuration = {}) {
  const train = Number(configuration.train_percent ?? 0);
  const validation = Number(configuration.validation_percent ?? 0);
  const test = Number(configuration.test_percent ?? 0);

  return train + validation + test;
}

/**
 * Check whether split percentages are valid.
 *
 * @param {Partial<DatasetSplitConfiguration>} configuration
 * @returns {boolean}
 */
export function isValidSplitConfiguration(configuration = {}) {
  const values = [
    Number(configuration.train_percent),
    Number(configuration.validation_percent),
    Number(configuration.test_percent),
  ];

  if (!values.every(Number.isFinite)) {
    return false;
  }

  if (values.some((value) => value < 0 || value > 100)) {
    return false;
  }

  return getSplitTotal(configuration) === 100;
}

/**
 * Check whether a split configuration can be submitted.
 *
 * @param {Partial<DatasetSplitConfiguration>} configuration
 * @returns {boolean}
 */
export function canCreateDatasetVersion(configuration = {}) {
  const seed = Number(configuration.random_seed);

  return (
    isValidSplitConfiguration(configuration) &&
    Number.isInteger(seed) &&
    seed >= 0 &&
    typeof configuration.stratified === "boolean"
  );
}

/**
 * Format split configuration for display.
 *
 * @param {Partial<DatasetSplitConfiguration>} configuration
 * @returns {string}
 */
export function formatSplitConfiguration(configuration = {}) {
  const train = Number(configuration.train_percent ?? 0);
  const validation = Number(configuration.validation_percent ?? 0);
  const test = Number(configuration.test_percent ?? 0);

  return `${train}/${validation}/${test}`;
}

// ============================================================================
// 15. DISPLAY HELPERS
// ============================================================================

/**
 * Convert a known ground-truth value into a display label.
 *
 * @param {string} value
 * @returns {string}
 */
export function getGroundTruthLabel(value) {
  if (value === DATASET_LABELS.NORMAL) {
    return "Normal";
  }

  if (value === DATASET_LABELS.BOMBING) {
    return "Bombing";
  }

  return "Unknown";
}

/**
 * Convert a known source value into a display label.
 *
 * @param {string} value
 * @returns {string}
 */
export function getDatasetSourceLabel(value) {
  return DATASET_SOURCE_LABELS[value] ?? "Unknown";
}

/**
 * Convert a known split value into a display label.
 *
 * @param {string} value
 * @returns {string}
 */
export function getDatasetSplitLabel(value) {
  const labels = {
    [DATASET_EXPORT_SPLIT.ALL]: "Entire Dataset",
    [DATASET_EXPORT_SPLIT.TRAIN]: "Training",
    [DATASET_EXPORT_SPLIT.VALIDATION]: "Validation",
    [DATASET_EXPORT_SPLIT.TEST]: "Testing",
  };

  return labels[value] ?? "Unknown";
}
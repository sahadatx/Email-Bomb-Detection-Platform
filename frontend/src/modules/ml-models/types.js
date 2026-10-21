/**
 * Module 07 — ML Model Management
 *
 * Shared API constants and JSDoc contracts. Field names and enum values in
 * this file mirror backend/app/modules/ml_models/schemas.py and the trainer.
 * Model type is a fixed API value because every supported engine is a classifier.
 */

// ============================================================================
// MODEL DEFINITIONS
// ============================================================================

/** Current backend engines all solve binary classification tasks. */
export const ML_MODEL_TYPE = Object.freeze({
  CLASSIFIER: "classifier",
});

export const ML_MODEL_TYPE_LABELS = Object.freeze({
  [ML_MODEL_TYPE.CLASSIFIER]: "Classifier",
});

export const ML_MODEL_STATUS = Object.freeze({
  ACTIVE: "active",
  INACTIVE: "inactive",
});

export const ML_MODEL_STATUS_LABELS = Object.freeze({
  [ML_MODEL_STATUS.ACTIVE]: "Active",
  [ML_MODEL_STATUS.INACTIVE]: "Inactive",
});

/** Algorithms registered by ModelTrainer.supported_algorithms. */
export const ML_ALGORITHMS = Object.freeze({
  DECISION_TREE: "decision_tree",
  LOGISTIC_REGRESSION: "logistic_regression",
  RANDOM_FOREST: "random_forest",
  SVM: "svm",
  WEIGHTED_SVM: "weighted_svm",
});

export const ML_ALGORITHM_LABELS = Object.freeze({
  [ML_ALGORITHMS.DECISION_TREE]: "Decision Tree",
  [ML_ALGORITHMS.LOGISTIC_REGRESSION]: "Logistic Regression",
  [ML_ALGORITHMS.RANDOM_FOREST]: "Random Forest",
  [ML_ALGORITHMS.SVM]: "SVM",
  [ML_ALGORITHMS.WEIGHTED_SVM]: "Weighted SVM",
});

/** @param {string|null|undefined} algorithm */
export function getAlgorithmLabel(algorithm) {
  if (!algorithm) return "Unknown";
  return ML_ALGORITHM_LABELS[algorithm] ?? algorithm;
}

/**
 * @typedef {Object} MLModel
 * @property {string} id UUID
 * @property {string} name Maximum 150 characters
 * @property {string|null} description
 * @property {"classifier"} model_type
 * @property {string} algorithm
 * @property {Record<string, *>} hyperparameters
 * @property {"active"|"inactive"} status
 * @property {string} created_at ISO datetime
 * @property {string} updated_at ISO datetime
 */

/** Actual POST /models request body. */
export const ML_MODEL_CREATE_FIELDS = Object.freeze([
  "name",
  "description",
  "algorithm",
  "hyperparameters",
]);

/**
 * @typedef {Object} MLModelCreate
 * @property {string} name Required, 1–150 characters
 * @property {string|null} [description]
 * @property {"classifier"} [model_type] Currently fixed by backend
 * @property {string} algorithm Required, maximum 100 characters
 * @property {Record<string, *>} [hyperparameters]
 */

/**
 * @typedef {Object} MLModelUpdate
 * @property {string} [name] 1–150 characters when supplied
 * @property {string|null} [description]
 * @property {Record<string, *>} [hyperparameters]
 */

/** @typedef {{status: "active"|"inactive"}} MLModelStatusUpdate */
/** @typedef {MLModel[]} MLModelListResponse GET /models returns an array. */
/** @typedef {{total: number}} MLModelCountResponse */

// ============================================================================
// TRAINING RUNS
// ============================================================================

export const TRAINING_RUN_STATUS = Object.freeze({
  PENDING: "pending",
  QUEUED: "queued",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELLED: "cancelled",
});

export const TRAINING_RUN_STATUS_LABELS = Object.freeze({
  [TRAINING_RUN_STATUS.PENDING]: "Pending",
  [TRAINING_RUN_STATUS.QUEUED]: "Queued",
  [TRAINING_RUN_STATUS.RUNNING]: "Running",
  [TRAINING_RUN_STATUS.COMPLETED]: "Completed",
  [TRAINING_RUN_STATUS.FAILED]: "Failed",
  [TRAINING_RUN_STATUS.CANCELLED]: "Cancelled",
});

// Retain the existing export used by TrainingProgress and TrainingRunTable.
export const TRAINING_STATUS_LABELS = TRAINING_RUN_STATUS_LABELS;

/**
 * @typedef {Object} MLTrainingRun
 * @property {string} id UUID
 * @property {string} model_definition_id UUID
 * @property {string} preprocessing_run_id UUID
 * @property {"pending"|"queued"|"running"|"completed"|"failed"|"cancelled"} status
 * @property {number} progress_percent 0–100; backend reported
 * @property {Record<string, *>} config_snapshot
 * @property {number} training_sample_count
 * @property {number} validation_sample_count
 * @property {number|null} duration_ms
 * @property {string|null} error_code
 * @property {string|null} error_message
 * @property {Record<string, *>} result_summary
 * @property {string|null} started_at ISO datetime
 * @property {string|null} completed_at ISO datetime
 * @property {string} created_at ISO datetime
 */

/**
 * @typedef {Object} MLTrainingRunCreate
 * @property {string} model_definition_id UUID
 * @property {string} preprocessing_run_id UUID
 * @property {Record<string, *>} [config_snapshot]
 */

/** @typedef {{items: MLTrainingRun[], total: number}} MLTrainingRunListResponse */

// ============================================================================
// MODEL VERSIONS / REGISTRY
// ============================================================================

export const MODEL_VERSION_STATUS = Object.freeze({
  REGISTERED: "registered",
  ACTIVE: "active",
  ARCHIVED: "archived",
});

export const MODEL_VERSION_STATUS_LABELS = Object.freeze({
  [MODEL_VERSION_STATUS.REGISTERED]: "Registered",
  [MODEL_VERSION_STATUS.ACTIVE]: "Active",
  [MODEL_VERSION_STATUS.ARCHIVED]: "Archived",
});

/**
 * @typedef {Object} MLModelVersion
 * @property {string} id UUID
 * @property {string} model_definition_id UUID
 * @property {string} training_run_id UUID
 * @property {number} version
 * @property {"registered"|"active"|"archived"} status
 * @property {string|null} artifact_filename
 * @property {string|null} storage_path
 * @property {string|null} media_type
 * @property {number} size_bytes
 * @property {string|null} checksum_sha256
 * @property {Record<string, *>} metadata_json
 * @property {string} created_at ISO datetime
 * @property {string|null} activated_at ISO datetime
 * @property {string|null} archived_at ISO datetime
 */

/** @typedef {{items: MLModelVersion[], total: number}} MLModelVersionListResponse */

// ============================================================================
// EVALUATION RUNS
// ============================================================================

export const EVALUATION_RUN_STATUS = Object.freeze({
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
  CANCELLED: "cancelled",
});

export const EVALUATION_RUN_STATUS_LABELS = Object.freeze({
  [EVALUATION_RUN_STATUS.PENDING]: "Pending",
  [EVALUATION_RUN_STATUS.RUNNING]: "Running",
  [EVALUATION_RUN_STATUS.COMPLETED]: "Completed",
  [EVALUATION_RUN_STATUS.FAILED]: "Failed",
  [EVALUATION_RUN_STATUS.CANCELLED]: "Cancelled",
});

// Retain the existing export used by ModelEvaluationPage.
export const EVALUATION_STATUS_LABELS = EVALUATION_RUN_STATUS_LABELS;

export const EVALUATION_SPLITS = Object.freeze({
  VALIDATION: "validation",
  TESTING: "testing",
});

export const EVALUATION_SPLIT_LABELS = Object.freeze({
  [EVALUATION_SPLITS.VALIDATION]: "Validation",
  [EVALUATION_SPLITS.TESTING]: "Testing",
});

// Retain the existing export used by ModelEvaluationPage.
export const EVALUATION_SPLIT = EVALUATION_SPLITS;

export const EVALUATION_METRICS = Object.freeze([
  "accuracy",
  "precision",
  "recall",
  "f1_score",
  "roc_auc",
]);

export const EVALUATION_METRIC_LABELS = Object.freeze({
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1_score: "F1 Score",
  roc_auc: "ROC-AUC",
});

/**
 * @typedef {Object} MLEvaluationRun
 * @property {string} id UUID
 * @property {string} model_version_id UUID
 * @property {string} preprocessing_run_id UUID
 * @property {"validation"|"testing"} evaluation_split
 * @property {"pending"|"running"|"completed"|"failed"|"cancelled"} status
 * @property {number} sample_count
 * @property {number|null} accuracy Range 0–1
 * @property {number|null} precision Range 0–1
 * @property {number|null} recall Range 0–1
 * @property {number|null} f1_score Range 0–1
 * @property {number|null} roc_auc Range 0–1
 * @property {Record<string, *>} confusion_matrix
 * @property {Record<string, *>} classification_report
 * @property {Record<string, *>} result_summary
 * @property {number|null} duration_ms
 * @property {string|null} error_code
 * @property {string|null} error_message
 * @property {string|null} started_at ISO datetime
 * @property {string|null} completed_at ISO datetime
 * @property {string} created_at ISO datetime
 */

/**
 * @typedef {Object} MLEvaluationRunCreate
 * @property {string} model_version_id UUID
 * @property {string} preprocessing_run_id UUID
 * @property {"validation"|"testing"} evaluation_split
 */

/** @typedef {{items: MLEvaluationRun[], total: number}} MLEvaluationRunListResponse */

// ============================================================================
// API QUERY PARAMETERS AND PAGINATION
// ============================================================================

/** Backend list routes accept offset >= 0 and limit 1–200. */
export const ML_MODEL_PAGINATION = Object.freeze({
  PAGE: 1,
  PAGE_SIZE: 30,
  MAX_PAGE_SIZE: 200,
});

/** Query keys match the actual FastAPI route parameters. */
export const ML_MODEL_QUERY = Object.freeze({
  OFFSET: "offset",
  LIMIT: "limit",
  STATUS: "status",
  ALGORITHM: "algorithm",
  MODEL_DEFINITION_ID: "model_definition_id",
  PREPROCESSING_RUN_ID: "preprocessing_run_id",
  MODEL_VERSION_ID: "model_version_id",
  EVALUATION_SPLIT: "evaluation_split",
});

export const ML_MODEL_FILTERS = Object.freeze({
  ALL_STATUSES: "all",
  ALL_ALGORITHMS: "all",
});

export const TRAINING_RUN_FILTERS = Object.freeze({
  ALL_STATUSES: "all",
});

export const MODEL_VERSION_FILTERS = Object.freeze({
  ALL_STATUSES: "all",
});

export const EVALUATION_RUN_FILTERS = Object.freeze({
  ALL_STATUSES: "all",
  ALL_SPLITS: "all",
});

/**
 * Route suffixes from backend/app/modules/ml_models/routes.py.
 * The application mounts these under /api/v1/ml-models.
 */
export const ML_MODEL_API_PATHS = Object.freeze({
  ALGORITHMS: "/algorithms",
  MODELS: "/models",
  MODEL_COUNT: "/models/count",
  MODEL_SUMMARY: "/models/summary",
  MODEL_TRAINING_RUNS: "/models/{model_id}/training-runs",
  TRAINING_RUNS: "/training-runs",
  TRAINING_RUN_RETRY: "/training-runs/{training_run_id}/retry",
  TRAINING_RUN_LOGS: "/training-runs/{training_run_id}/logs",
  MODEL_VERSIONS: "/versions",
  MODEL_VERSION_ACTIVATE: "/versions/{version_id}/activate",
  MODEL_VERSION_ARCHIVE: "/versions/{version_id}/archive",
  MODEL_VERSION_RESTORE: "/versions/{version_id}/restore",
  MODEL_VERSION_ARTIFACT: "/versions/{version_id}/artifact",
  EVALUATION_RUNS: "/evaluation-runs",
  EVALUATION_REPORT_EXPORT: "/evaluation-runs/{evaluation_run_id}/export",
});

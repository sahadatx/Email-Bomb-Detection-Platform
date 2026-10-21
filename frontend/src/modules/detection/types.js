/**
 * Detection & Risk Analysis API constants and JSDoc contracts.
 * Keep the field names synchronized with backend/app/modules/detection/schemas.py.
 */

export const DETECTION_LABELS = Object.freeze({
  bomb: "Email Bomb",
  normal: "Normal",
  unknown: "Unavailable",
});

export const DETECTION_STATUSES = Object.freeze({
  COMPLETED: "completed",
  FAILED: "failed",
});

export const RISK_LEVELS = Object.freeze([
  "critical",
  "high",
  "medium",
  "low",
  "unavailable",
]);

export const DETECTION_PERIODS = Object.freeze(["24h", "7d", "30d"]);
export const DETECTION_PAGE_SIZE = 30;
export const DETECTION_MAX_UPLOAD_BYTES = 2_000_000;

/** @typedef {"bomb"|"normal"|"unknown"} DetectionPrediction */
/** @typedef {"critical"|"high"|"medium"|"low"|"unavailable"} RiskLevel */

/**
 * @typedef {Object} RiskFactor
 * @property {string} name
 * @property {string|number|boolean|null} value
 * @property {string} impact
 * @property {number} points
 */

/**
 * @typedef {Object} RiskAssessment
 * @property {number|null} score
 * @property {RiskLevel} level
 * @property {RiskFactor[]} factors
 * @property {"completed"|"failed"} status
 */

/**
 * @typedef {Object} BehavioralAnomaly
 * @property {string} pattern
 * @property {"low"|"medium"|"high"|"critical"} severity
 * @property {string} description
 */

/**
 * @typedef {Object} BehavioralResult
 * @property {"completed"|"failed"|"disabled"|"insufficient_data"} status
 * @property {string} summary
 * @property {Record<string, number|string|boolean|null>} metrics
 * @property {BehavioralAnomaly[]} anomalies
 */

/**
 * @typedef {Object} DetectionRecord
 * @property {string} id
 * @property {string|null} email_id
 * @property {string|null} input_id
 * @property {string|null} input_filename
 * @property {string} model_version_id
 * @property {DetectionPrediction} predicted_label
 * @property {number|null} confidence
 * @property {"completed"|"failed"} status
 * @property {Record<string, unknown>} feature_snapshot
 * @property {string|null} error_message
 * @property {string} created_at
 * @property {string|null} email_subject
 * @property {string|null} sender
 * @property {string|null} model_name
 * @property {number|null} version
 * @property {RiskAssessment|null} risk
 * @property {BehavioralResult|null} behavioral
 */

/**
 * @typedef {Object} DetectionListResponse
 * @property {DetectionRecord[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} page_size
 */

/**
 * @typedef {Object} DetectionCreateRequest
 * @property {string} email_id
 * @property {string=} model_version_id
 * @property {boolean=} run_behavioral_analysis
 * @property {boolean=} calculate_risk_score
 */

/**
 * @typedef {Object} DetectionEmailOption
 * @property {string} id
 * @property {string|null} sender
 * @property {string|null} subject
 * @property {"ready"|"features_missing"|"features_failed"} status
 * @property {boolean} has_features
 */

/**
 * @typedef {Object} ActiveModelVersion
 * @property {string} model_version_id
 * @property {string} model_name
 * @property {string} algorithm
 * @property {number} version
 */

/**
 * @typedef {Object} DetectionSettings
 * @property {string|null} default_model_version_id
 * @property {number} high_risk_threshold
 * @property {number} critical_risk_threshold
 * @property {boolean} enable_behavioral_analysis
 * @property {boolean} save_feature_snapshots
 * @property {boolean} store_detection_history
 */

/**
 * @typedef {Object} DetectionOverview
 * @property {number} total_detections
 * @property {number} bomb_detected
 * @property {number} normal_emails
 * @property {number} high_risk
 * @property {{time:string,count:number}[]} activity
 * @property {DetectionRecord[]} recent
 */

/**
 * @typedef {Object} RiskSummary
 * @property {Record<RiskLevel, number>} distribution
 * @property {{name:string,occurrences:number,impact:string|null,detection_ids:string[]}[]} factors
 */

/**
 * @typedef {Object} BehavioralSummary
 * @property {number} emails_analyzed
 * @property {number} anomalies
 * @property {BehavioralAnomaly[]} patterns
 */

/**
 * @typedef {Object} BehavioralActivity
 * @property {"24h"|"7d"|"30d"} period
 * @property {{time:string,emails:number}[]} activity
 */

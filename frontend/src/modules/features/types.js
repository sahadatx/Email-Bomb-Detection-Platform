/**
 * Module 04 — Feature Engineering
 *
 * Frontend data contracts for the F1-F12 Feature Engineering API.
 *
 * Responsibilities:
 * - Feature constants
 * - Feature definitions
 * - Feature status/source/level contracts
 * - Feature vector helpers
 * - API response normalization
 * - Workspace item normalization
 * - Workspace filter normalization
 * - Pagination helpers
 * - Extraction request builders
 * - Extraction response normalization
 * - Global selection helpers
 * - Feature Details drawer helpers
 *
 * This file contains no:
 * - API calls
 * - UI rendering
 * - ML/classification
 * - prediction
 * - confidence
 * - risk scoring
 * - threat scoring
 */

// ============================================================
// MODULE CONSTANTS
// ============================================================

export const FEATURE_COUNT = 12;

export const DEFAULT_PAGE = 1;

export const DEFAULT_PAGE_SIZE = 30;

export const MAX_PAGE_SIZE = 100;


// ============================================================
// PUBLIC FEATURE STATUS
// ============================================================

export const FEATURE_STATUS = Object.freeze({
  PENDING: "pending",
  EXTRACTED: "extracted",
  WARNING: "warning",
  FAILED: "failed",
});

export const FEATURE_STATUSES = Object.freeze([
  FEATURE_STATUS.PENDING,
  FEATURE_STATUS.EXTRACTED,
  FEATURE_STATUS.WARNING,
  FEATURE_STATUS.FAILED,
]);


// ============================================================
// FEATURE SOURCE
// ============================================================

export const FEATURE_SOURCE = Object.freeze({
  FILE_UPLOAD: "file_upload",
  RAW_EMAIL: "raw_email",
});

export const FEATURE_SOURCES = Object.freeze([
  FEATURE_SOURCE.FILE_UPLOAD,
  FEATURE_SOURCE.RAW_EMAIL,
]);


// ============================================================
// FEATURE LEVEL
// ============================================================
//
// Level represents Module 02 ground-truth classification.
//
// This is NOT an ML prediction.
//

export const FEATURE_LEVEL = Object.freeze({
  NORMAL: "normal",
  BOMBING: "bombing",
});

export const FEATURE_LEVELS = Object.freeze([
  FEATURE_LEVEL.NORMAL,
  FEATURE_LEVEL.BOMBING,
]);


// ============================================================
// F1-F12 IDENTIFIERS
// ============================================================

export const FEATURE_IDS = Object.freeze([
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


// ============================================================
// FEATURE DEFINITIONS
// ============================================================
//
// Locked Module 04 F1-F12 semantics.
//

export const FEATURE_DEFINITIONS = Object.freeze([
  {
    id: "F1",
    key: "f1_sender_email",
    name: "Sender Email",
    dataType: "string",
    source: "sender",
    description:
      "Extracted sender email address from the From header field.",
  },

  {
    id: "F2",
    key: "f2_known_domain",
    name: "Known Domain Indicator",
    dataType: "boolean",
    source: "sender",
    description:
      "Identifies whether the sender domain belongs to trusted providers.",
  },

  {
    id: "F3",
    key: "f3_message_id",
    name: "Message-ID Presence",
    dataType: "boolean",
    source: "header",
    description:
      "Checks the existence of a valid Message-ID header.",
  },

  {
    id: "F4",
    key: "f4_auto_submitted",
    name: "Auto-Submitted Header",
    dataType: "boolean",
    source: "header",
    description:
      "Detects automatically generated emails.",
  },

  {
    id: "F5",
    key: "f5_precedence_bulk",
    name: "Precedence Bulk Indicator",
    dataType: "boolean",
    source: "header",
    description:
      "Identifies bulk mailing behavior using the Precedence header.",
  },

  {
    id: "F6",
    key: "f6_list_id",
    name: "List-Id Header",
    dataType: "boolean",
    source: "header",
    description:
      "Detects mailing list identifiers in emails.",
  },

  {
    id: "F7",
    key: "f7_x_beenthere",
    name: "X-BeenThere Header",
    dataType: "boolean",
    source: "header",
    description:
      "Identifies mailing list traversal headers.",
  },

  {
    id: "F8",
    key: "f8_x_anti_abuse",
    name: "X-Anti-Abuse Header",
    dataType: "boolean",
    source: "header",
    description:
      "Detects abuse or spam-related tracking headers.",
  },

  {
    id: "F9",
    key: "f9_keyword_features",
    name: "Keyword-Based Content Features",
    dataType: "integer",
    source: "content",
    description:
      "Detects configured suspicious keywords in the normalized subject and text body.",
  },

  {
    id: "F10",
    key: "f10_subject_length",
    name: "Subject Length",
    dataType: "integer",
    source: "content",
    description:
      "Measures the length of the email subject.",
  },

  {
    id: "F11",
    key: "f11_emails_per_minute",
    name: "Emails Per Minute",
    dataType: "integer",
    source: "temporal",
    description:
      "Calculates the number of emails received per minute.",
  },

  {
    id: "F12",
    key: "f12_emails_per_hour",
    name: "Emails Per Hour",
    dataType: "integer",
    source: "temporal",
    description:
      "Calculates the number of emails received per hour.",
  },
]);

export const FEATURE_DEFINITION_MAP = Object.freeze(
  Object.fromEntries(
    FEATURE_DEFINITIONS.map(
      (definition) => [
        definition.id,
        definition,
      ],
    ),
  ),
);


// ============================================================
// TYPE / ID HELPERS
// ============================================================

export function isFeatureId(value) {
  return FEATURE_IDS.includes(value);
}

export function isFeatureStatus(value) {
  return FEATURE_STATUSES.includes(value);
}

export function isFeatureSource(value) {
  return FEATURE_SOURCES.includes(value);
}

export function isFeatureLevel(value) {
  return FEATURE_LEVELS.includes(value);
}

export function getFeatureDefinition(featureId) {
  return (
    FEATURE_DEFINITION_MAP[featureId] ??
    null
  );
}

export function getFeatureKey(featureId) {
  return (
    getFeatureDefinition(featureId)?.key ??
    null
  );
}


// ============================================================
// FEATURE VALUE NORMALIZATION
// ============================================================

export function normalizeFeatureValue(value) {
  if (
    value === undefined ||
    value === null
  ) {
    return null;
  }

  return value;
}

export function formatFeatureValue(value) {
  if (
    value === undefined ||
    value === null
  ) {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}


// ============================================================
// EMPTY FEATURE VECTOR
// ============================================================

export function createEmptyFeatureVector() {
  return {
    f1_sender_email: null,

    f2_known_domain: false,

    f3_message_id: false,

    f4_auto_submitted: false,

    f5_precedence_bulk: false,

    f6_list_id: false,

    f7_x_beenthere: false,

    f8_x_anti_abuse: false,

    f9_keyword_features: 0,

    f10_subject_length: 0,

    f11_emails_per_minute: 0,

    f12_emails_per_hour: 0,
  };
}


// ============================================================
// FEATURE VECTOR NORMALIZATION
// ============================================================

export function normalizeFeatureVector(featureVector) {
  const source = featureVector ?? {};

  return {
    ...createEmptyFeatureVector(),
    ...source,
  };
}


// ============================================================
// FEATURE VECTOR → DISPLAY VALUES
// ============================================================

export function getFeatureVectorValues(featureVector) {
  const vector =
    normalizeFeatureVector(featureVector);

  return FEATURE_DEFINITIONS.map(
    (definition) => ({
      id: definition.id,

      key: definition.key,

      name: definition.name,

      dataType: definition.dataType,

      source: definition.source,

      description: definition.description,

      value:
        normalizeFeatureValue(
          vector[definition.key],
        ),
    }),
  );
}


// ============================================================
// DETAIL FEATURE VALUE NORMALIZATION
// ============================================================

export function normalizeFeatureValueItem(item) {
  if (!item) {
    return null;
  }

  return {
    featureId:
      item.feature_id ??
      item.id ??
      null,

    featureName:
      item.feature_name ??
      item.name ??
      "",

    value:
      normalizeFeatureValue(
        item.value,
      ),

    dataType:
      item.data_type ??
      "",

    source:
      item.source ??
      "",

    status:
      item.status ??
      "valid",

    description:
      item.description ??
      "",

    calculation:
      item.calculation ??
      "",

    rawValue:
      normalizeFeatureValue(
        item.raw_value,
      ),

    displayValue:
      item.display_value ??
      formatFeatureValue(
        item.value,
      ),
  };
}

export function normalizeFeatureValues(values) {
  if (!Array.isArray(values)) {
    return [];
  }

  return values
    .map(normalizeFeatureValueItem)
    .filter(Boolean);
}


// ============================================================
// IDENTITY NORMALIZATION
// ============================================================

export function normalizeFeatureIdentity(response) {
  const identity =
    response?.identity ??
    {};

  return {
    emailId:
      identity.email_id ??
      response?.email_id ??
      null,

    sender:
      identity.sender ??
      response?.sender ??
      null,

    subject:
      identity.subject ??
      response?.subject ??
      null,

    messageId:
      identity.message_id ??
      response?.message_id ??
      null,

    source:
      identity.source ??
      response?.source ??
      null,

    sourceIdentifier:
      identity.source_identifier ??
      response?.source_identifier ??
      null,

    level:
      identity.level ??
      response?.level ??
      null,
  };
}


// ============================================================
// TIMESTAMP NORMALIZATION
// ============================================================

export function normalizeFeatureTimestamps(response) {
  const timestamps =
    response?.timestamps ??
    {};

  return {
    receivedAt:
      timestamps.received_at ??
      response?.received_at ??
      null,

    collectedAt:
      timestamps.collected_at ??
      response?.collected_at ??
      null,

    parsedAt:
      timestamps.parsed_at ??
      response?.parsed_at ??
      null,

    extractedAt:
      timestamps.extracted_at ??
      response?.extracted_at ??
      null,
  };
}


// ============================================================
// VALIDATION NORMALIZATION
// ============================================================

export function normalizeFeatureValidation(response) {
  const validation =
    response?.validation ??
    {};

  return {
    errors:
      Array.isArray(
        validation.errors,
      )
        ? validation.errors
        : [],

    warnings:
      Array.isArray(
        validation.warnings,
      )
        ? validation.warnings
        : [],

    isValid:
      validation.is_valid ??
      true,
  };
}


// ============================================================
// EXTRACTION METADATA NORMALIZATION
// ============================================================

export function normalizeFeatureMetadata(response) {
  const metadata =
    response?.metadata ??
    {};

  const rawStatus =
    metadata.status ??
    response?.feature_status ??
    FEATURE_STATUS.PENDING;

  return {
    extractorVersion:
      metadata.extractor_version ??
      null,

    processingTimeMs:
      Number(
        metadata.processing_time_ms,
      ) || 0,

    status:
      isFeatureStatus(rawStatus)
        ? rawStatus
        : FEATURE_STATUS.PENDING,

    extractedAt:
      metadata.extracted_at ??
      response?.extracted_at ??
      null,
  };
}


// ============================================================
// COMPLETE FEATURE RESPONSE
// ============================================================

export function normalizeFeatureResponse(response) {
  if (!response) {
    return null;
  }

  return {
    id:
      response.id ??
      null,

    emailId:
      response.email_id ??
      null,

    identity:
      normalizeFeatureIdentity(
        response,
      ),

    timestamps:
      normalizeFeatureTimestamps(
        response,
      ),

    featureVector:
      normalizeFeatureVector(
        response.feature_vector,
      ),

    features:
      normalizeFeatureValues(
        response.features,
      ),

    validation:
      normalizeFeatureValidation(
        response,
      ),

    metadata:
      normalizeFeatureMetadata(
        response,
      ),
  };
}


// ============================================================
// WORKSPACE FILTERS
// ============================================================

export function createEmptyWorkspaceFilters() {
  return {
    search: null,

    source: null,

    level: null,

    status: null,

    fromDate: null,

    toDate: null,
  };
}

export function normalizeWorkspaceFilterDate(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return null;
  }

  if (value instanceof Date) {
    if (
      Number.isNaN(
        value.getTime(),
      )
    ) {
      return null;
    }

    const year =
      value.getFullYear();

    const month =
      String(
        value.getMonth() + 1,
      ).padStart(2, "0");

    const day =
      String(
        value.getDate(),
      ).padStart(2, "0");

    return `${year}-${month}-${day}`;
  }

  const normalized =
    String(value).trim();

  if (!normalized) {
    return null;
  }

  return normalized.slice(0, 10);
}

export function normalizeWorkspaceFilters(
  filters = {},
) {
  const source =
    filters ?? {};

  const normalizedSource =
    source.source ??
    null;

  const normalizedLevel =
    source.level ??
    null;

  const normalizedStatus =
    source.status ??
    null;

  return {
    search:
      source.search
        ? String(
            source.search,
          ).trim() || null
        : null,

    source:
      isFeatureSource(
        normalizedSource,
      )
        ? normalizedSource
        : null,

    level:
      isFeatureLevel(
        normalizedLevel,
      )
        ? normalizedLevel
        : null,

    status:
      isFeatureStatus(
        normalizedStatus,
      )
        ? normalizedStatus
        : null,

    fromDate:
      normalizeWorkspaceFilterDate(
        source.fromDate ??
        source.from_date,
      ),

    toDate:
      normalizeWorkspaceFilterDate(
        source.toDate ??
        source.to_date,
      ),
  };
}

export function hasActiveWorkspaceFilters(
  filters = {},
) {
  const normalized =
    normalizeWorkspaceFilters(
      filters,
    );

  return Boolean(
    normalized.search ||
    normalized.source ||
    normalized.level ||
    normalized.status ||
    normalized.fromDate ||
    normalized.toDate,
  );
}


// ============================================================
// WORKSPACE ITEM NORMALIZATION
// ============================================================

export function normalizeFeatureListItem(item) {
  if (!item) {
    return null;
  }

  const featureStatus =
    isFeatureStatus(
      item.feature_status,
    )
      ? item.feature_status
      : FEATURE_STATUS.PENDING;

  const source =
    isFeatureSource(item.source)
      ? item.source
      : null;

  const level =
    isFeatureLevel(item.level)
      ? item.level
      : null;

  const parsed =
    Boolean(item.parsed);

  const featureCount =
    Number.isInteger(
      item.feature_count,
    )
      ? Math.max(
          0,
          Math.min(
            item.feature_count,
            FEATURE_COUNT,
          ),
        )
      : 0;

  const totalFeatures =
    Number.isInteger(
      item.total_features,
    )
      ? Math.max(
          FEATURE_COUNT,
          item.total_features,
        )
      : FEATURE_COUNT;

  return {
    emailId:
      item.email_id ??
      null,

    subject:
      item.subject ??
      null,

    sender:
      item.sender ??
      null,

    messageId:
      item.message_id ??
      null,

    source,

    sourceIdentifier:
      item.source_identifier ??
      null,

    level,

    receivedAt:
      item.received_at ??
      null,

    collectedAt:
      item.collected_at ??
      null,

    parsedAt:
      item.parsed_at ??
      null,

    parsed,

    featureStatus,

    featureCount,

    totalFeatures,

    hasFeatures:
      Boolean(
        item.has_features,
      ),

    updatedAt:
      item.updated_at ??
      null,
  };
}


// ============================================================
// PAGINATION
// ============================================================

export function createEmptyPagination() {
  return {
    page: DEFAULT_PAGE,

    pageSize:
      DEFAULT_PAGE_SIZE,

    total: 0,

    totalPages: 0,

    hasPrevious: false,

    hasNext: false,
  };
}

export function normalizePagination(
  pagination,
) {
  if (!pagination) {
    return createEmptyPagination();
  }

  const page =
    Number.isInteger(
      pagination.page,
    )
      ? Math.max(
          1,
          pagination.page,
        )
      : DEFAULT_PAGE;

  const pageSize =
    Number.isInteger(
      pagination.page_size,
    )
      ? Math.min(
          Math.max(
            pagination.page_size,
            1,
          ),
          MAX_PAGE_SIZE,
        )
      : DEFAULT_PAGE_SIZE;

  const total =
    Number.isInteger(
      pagination.total,
    )
      ? Math.max(
          0,
          pagination.total,
        )
      : 0;

  const calculatedTotalPages =
    total > 0
      ? Math.ceil(
          total / pageSize,
        )
      : 0;

  const totalPages =
    Number.isInteger(
      pagination.total_pages,
    )
      ? Math.max(
          0,
          pagination.total_pages,
        )
      : calculatedTotalPages;

  return {
    page,

    pageSize,

    total,

    totalPages,

    hasPrevious:
      Boolean(
        pagination.has_previous,
      ),

    hasNext:
      Boolean(
        pagination.has_next,
      ),
  };
}


// ============================================================
// WORKSPACE RESPONSE FILTER NORMALIZATION
// ============================================================

export function normalizeWorkspaceResponseFilters(
  filters,
) {
  return normalizeWorkspaceFilters(
    filters,
  );
}


// ============================================================
// WORKSPACE RESPONSE
// ============================================================

export function normalizeFeatureListResponse(
  response,
) {
  if (!response) {
    return {
      items: [],

      pagination:
        createEmptyPagination(),

      filters:
        createEmptyWorkspaceFilters(),
    };
  }

  return {
    items:
      Array.isArray(
        response.items,
      )
        ? response.items
            .map(
              normalizeFeatureListItem,
            )
            .filter(Boolean)
        : [],

    pagination:
      normalizePagination(
        response.pagination,
      ),

    filters:
      normalizeWorkspaceResponseFilters(
        response.filters,
      ),
  };
}


// ============================================================
// FEATURE SELECTION RESPONSE
// ============================================================
//
// Backend contract:
//
// {
//   total_matching: number,
//   total_selectable: number,
//   email_ids: UUID[],
//   filters: {
//     search,
//     source,
//     level,
//     status,
//     from_date,
//     to_date
//   }
// }
//
// Selection is resolved against the COMPLETE filtered result
// set, not just the currently visible page.
//

export function normalizeFeatureSelectionResponse(
  response,
) {
  if (!response) {
    return {
      totalMatching: 0,

      totalSelectable: 0,

      emailIds: [],

      filters:
        createEmptyWorkspaceFilters(),
    };
  }

  const rawEmailIds =
    Array.isArray(
      response.email_ids,
    )
      ? response.email_ids
      : [];

  const emailIds = [
    ...new Set(
      rawEmailIds
        .map(
          (emailId) => {
            if (
              emailId === null ||
              emailId === undefined
            ) {
              return null;
            }

            const normalized =
              String(
                emailId,
              ).trim();

            return normalized || null;
          },
        )
        .filter(Boolean),
    ),
  ];

  const totalMatching =
    Math.max(
      0,
      Number(
        response.total_matching,
      ) || 0,
    );

  const totalSelectable =
    Math.max(
      0,
      Number(
        response.total_selectable,
      ) || emailIds.length,
    );

  return {
    totalMatching,

    totalSelectable,

    emailIds,

    filters:
      normalizeWorkspaceFilters(
        response.filters,
      ),
  };
}


// ============================================================
// SUMMARY
// ============================================================

export function createEmptyFeatureSummary() {
  return {
    totalCollected: 0,

    totalParsed: 0,

    totalFeaturesReady: 0,

    totalPending: 0,

    totalWarnings: 0,

    totalFailed: 0,

    readinessPercentage: 0,
  };
}

export function normalizeFeatureSummary(
  response,
) {
  const summary =
    response?.summary ??
    response ??
    {};

  return {
    totalCollected:
      Number(
        summary.total_collected,
      ) || 0,

    totalParsed:
      Number(
        summary.total_parsed,
      ) || 0,

    totalFeaturesReady:
      Number(
        summary.total_features_ready,
      ) || 0,

    totalPending:
      Number(
        summary.total_pending,
      ) || 0,

    totalWarnings:
      Number(
        summary.total_warnings,
      ) || 0,

    totalFailed:
      Number(
        summary.total_failed,
      ) || 0,

    readinessPercentage:
      Number(
        summary.readiness_percentage,
      ) || 0,
  };
}


// ============================================================
// EXTRACTION REQUEST BUILDERS
// ============================================================

export function buildExtractionRequest(
  force = false,
) {
  return {
    force: Boolean(force),
  };
}

export const createFeatureExtractionRequest =
  buildExtractionRequest;


export function buildBatchExtractionRequest(
  emailIds = [],
  force = false,
) {
  const normalizedIds =
    Array.isArray(emailIds)
      ? emailIds
          .map(
            (emailId) => {
              if (
                emailId === null ||
                emailId === undefined
              ) {
                return null;
              }

              const normalized =
                String(
                  emailId,
                ).trim();

              return normalized || null;
            },
          )
          .filter(Boolean)
      : [];

  return {
    email_ids: [
      ...new Set(
        normalizedIds,
      ),
    ],

    force: Boolean(force),
  };
}

export const createBatchExtractionRequest =
  buildBatchExtractionRequest;


// ============================================================
// EXTRACTION OPERATION SUMMARY
// ============================================================

export function normalizeExtractionSummary(
  summary,
) {
  return {
    selected:
      Number(
        summary?.selected,
      ) || 0,

    extracted:
      Number(
        summary?.extracted,
      ) || 0,

    warnings:
      Number(
        summary?.warnings,
      ) || 0,

    failed:
      Number(
        summary?.failed,
      ) || 0,
  };
}


// ============================================================
// EXTRACTION RESPONSE
// ============================================================

export function normalizeExtractionResponse(
  response,
) {
  return {
    summary:
      normalizeExtractionSummary(
        response?.summary,
      ),

    results:
      Array.isArray(
        response?.results,
      )
        ? response.results
            .map(
              normalizeFeatureResponse,
            )
            .filter(Boolean)
        : [],
  };
}


// ============================================================
// HEALTH
// ============================================================

export function normalizeFeatureHealth(
  response,
) {
  return {
    status:
      response?.status ??
      "unknown",

    module:
      response?.module ??
      "feature-engineering",

    featureSchema:
      response?.feature_schema ??
      "F1-F12",

    featureCount:
      Number(
        response?.feature_count,
      ) || FEATURE_COUNT,
  };
}


// ============================================================
// DEFINITIONS
// ============================================================

export function normalizeDefinition(
  definition,
) {
  if (!definition) {
    return null;
  }

  return {
    featureId:
      definition.feature_id ??
      definition.id ??
      null,

    name:
      definition.name ??
      "",

    description:
      definition.description ??
      "",

    dataType:
      definition.data_type ??
      "",

    source:
      definition.source ??
      "",

    calculation:
      definition.calculation ??
      "",

    missingValue:
      definition.missing_value ??
      "",

    normalization:
      definition.normalization ??
      "",
  };
}

export function normalizeDefinitionsResponse(
  response,
) {
  return {
    definitions:
      Array.isArray(
        response?.definitions,
      )
        ? response.definitions
            .map(
              normalizeDefinition,
            )
            .filter(Boolean)
        : [],

    total:
      Number(
        response?.total,
      ) || 0,
  };
}

export const normalizeFeatureDefinitions =
  normalizeDefinitionsResponse;


// ============================================================
// STATUS LABEL HELPERS
// ============================================================

export function getFeatureStatusLabel(
  status,
) {
  switch (status) {
    case FEATURE_STATUS.PENDING:
      return "Pending";

    case FEATURE_STATUS.EXTRACTED:
      return "Extracted";

    case FEATURE_STATUS.WARNING:
      return "Warning";

    case FEATURE_STATUS.FAILED:
      return "Failed";

    default:
      return "Unknown";
  }
}

export function getFeatureSourceLabel(
  source,
) {
  switch (source) {
    case FEATURE_SOURCE.FILE_UPLOAD:
      return "File Upload";

    case FEATURE_SOURCE.RAW_EMAIL:
      return "Raw Email";

    default:
      return "—";
  }
}

export function getFeatureLevelLabel(
  level,
) {
  switch (level) {
    case FEATURE_LEVEL.NORMAL:
      return "Normal";

    case FEATURE_LEVEL.BOMBING:
      return "Bombing";

    default:
      return "—";
  }
}


// ============================================================
// FEATURE STATE HELPERS
// ============================================================

export function isFeatureReady(
  status,
) {
  return (
    status ===
      FEATURE_STATUS.EXTRACTED ||
    status ===
      FEATURE_STATUS.WARNING
  );
}

export function isFeaturePending(
  status,
) {
  return (
    status ===
    FEATURE_STATUS.PENDING
  );
}

export function isFeatureFailed(
  status,
) {
  return (
    status ===
    FEATURE_STATUS.FAILED
  );
}


// ============================================================
// SELECTION ELIGIBILITY
// ============================================================
//
// A row is selectable when feature extraction can still be
// performed.
//
// Eligible:
// - pending
// - warning
// - failed
//
// Not eligible:
// - extracted
//

export function isFeatureSelectable(
  item,
) {
  if (!item) {
    return false;
  }

  return (
    item.featureStatus ===
      FEATURE_STATUS.PENDING ||
    item.featureStatus ===
      FEATURE_STATUS.WARNING ||
    item.featureStatus ===
      FEATURE_STATUS.FAILED
  );
}


export function getSelectableFeatureIds(
  items = [],
) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter(
      isFeatureSelectable,
    )
    .map(
      (item) =>
        item?.emailId ??
        null,
    )
    .filter(Boolean);
}


export function getPendingFeatureIds(
  items = [],
) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter(
      (item) =>
        item?.featureStatus ===
        FEATURE_STATUS.PENDING,
    )
    .map(
      (item) =>
        item?.emailId ??
        null,
    )
    .filter(Boolean);
}


export function getFailedFeatureIds(
  items = [],
) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter(
      (item) =>
        item?.featureStatus ===
        FEATURE_STATUS.FAILED,
    )
    .map(
      (item) =>
        item?.emailId ??
        null,
    )
    .filter(Boolean);
}


export function getWarningFeatureIds(
  items = [],
) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter(
      (item) =>
        item?.featureStatus ===
        FEATURE_STATUS.WARNING,
    )
    .map(
      (item) =>
        item?.emailId ??
        null,
    )
    .filter(Boolean);
}


// ============================================================
// SELECTION HELPERS
// ============================================================

export function normalizeSelectedIds(
  selectedIds = [],
) {
  if (!Array.isArray(selectedIds)) {
    return [];
  }

  return [
    ...new Set(
      selectedIds
        .map(
          (emailId) => {
            if (
              emailId === null ||
              emailId === undefined
            ) {
              return null;
            }

            const normalized =
              String(
                emailId,
              ).trim();

            return normalized || null;
          },
        )
        .filter(Boolean),
    ),
  ];
}


export function toggleSelectedId(
  selectedIds = [],
  emailId,
) {
  const current =
    normalizeSelectedIds(
      selectedIds,
    );

  if (
    emailId === null ||
    emailId === undefined
  ) {
    return current;
  }

  const normalizedId =
    String(
      emailId,
    ).trim();

  if (!normalizedId) {
    return current;
  }

  if (
    current.includes(
      normalizedId,
    )
  ) {
    return current.filter(
      (id) =>
        id !== normalizedId,
    );
  }

  return [
    ...current,
    normalizedId,
  ];
}


export function areAllIdsSelected(
  selectedIds = [],
  candidateIds = [],
) {
  const candidates =
    normalizeSelectedIds(
      candidateIds,
    );

  if (
    candidates.length === 0
  ) {
    return false;
  }

  const selected =
    new Set(
      normalizeSelectedIds(
        selectedIds,
      ),
    );

  return candidates.every(
    (id) =>
      selected.has(id),
  );
}


export function selectAllIds(
  selectedIds = [],
  candidateIds = [],
) {
  return [
    ...new Set([
      ...normalizeSelectedIds(
        selectedIds,
      ),
      ...normalizeSelectedIds(
        candidateIds,
      ),
    ]),
  ];
}


export function removeIds(
  selectedIds = [],
  idsToRemove = [],
) {
  const selected =
    normalizeSelectedIds(
      selectedIds,
    );

  const remove =
    new Set(
      normalizeSelectedIds(
        idsToRemove,
      ),
    );

  return selected.filter(
    (id) =>
      !remove.has(id),
  );
}


export function clearSelectedIds() {
  return [];
}


// ============================================================
// GLOBAL SELECTION STATE HELPERS
// ============================================================

export function createEmptySelectionState() {
  return {
    selectedEmailIds: [],

    totalMatching: 0,

    totalSelectable: 0,

    filters:
      createEmptyWorkspaceFilters(),
  };
}


export function normalizeSelectionState(
  selection,
) {
  if (!selection) {
    return createEmptySelectionState();
  }

  return {
    selectedEmailIds:
      normalizeSelectedIds(
        selection.selectedEmailIds ??
        selection.emailIds ??
        [],
      ),

    totalMatching:
      Math.max(
        0,
        Number(
          selection.totalMatching,
        ) || 0,
      ),

    totalSelectable:
      Math.max(
        0,
        Number(
          selection.totalSelectable,
        ) || 0,
      ),

    filters:
      normalizeWorkspaceFilters(
        selection.filters,
      ),
  };
}


export function isGlobalSelectionComplete(
  selectedIds = [],
  totalSelectable = 0,
) {
  const selected =
    normalizeSelectedIds(
      selectedIds,
    );

  const total =
    Math.max(
      0,
      Number(totalSelectable) || 0,
    );

  return (
    total > 0 &&
    selected.length >= total
  );
}


// ============================================================
// DETAIL DRAWER HELPERS
// ============================================================
//
// Module 04 Feature Details is displayed in a right-side
// drawer, not as a separate page.
//

export function createEmptyFeatureDetails() {
  return {
    id: null,

    emailId: null,

    identity: {
      emailId: null,
      sender: null,
      subject: null,
      messageId: null,
      source: null,
      sourceIdentifier: null,
      level: null,
    },

    timestamps: {
      receivedAt: null,
      collectedAt: null,
      parsedAt: null,
      extractedAt: null,
    },

    featureVector:
      createEmptyFeatureVector(),

    features: [],

    validation: {
      errors: [],
      warnings: [],
      isValid: true,
    },

    metadata: {
      extractorVersion: null,
      processingTimeMs: 0,
      status:
        FEATURE_STATUS.PENDING,
      extractedAt: null,
    },
  };
}


export function hasFeatureDetails(
  feature,
) {
  return Boolean(
    feature?.emailId,
  );
}


// ============================================================
// DEFAULT EXPORT
// ============================================================

export default {
  FEATURE_COUNT,

  DEFAULT_PAGE,

  DEFAULT_PAGE_SIZE,

  MAX_PAGE_SIZE,

  FEATURE_STATUS,

  FEATURE_STATUSES,

  FEATURE_SOURCE,

  FEATURE_SOURCES,

  FEATURE_LEVEL,

  FEATURE_LEVELS,

  FEATURE_IDS,

  FEATURE_DEFINITIONS,

  FEATURE_DEFINITION_MAP,

  isFeatureId,

  isFeatureStatus,

  isFeatureSource,

  isFeatureLevel,

  getFeatureDefinition,

  getFeatureKey,

  normalizeFeatureValue,

  formatFeatureValue,

  createEmptyFeatureVector,

  normalizeFeatureVector,

  getFeatureVectorValues,

  normalizeFeatureValueItem,

  normalizeFeatureValues,

  normalizeFeatureIdentity,

  normalizeFeatureTimestamps,

  normalizeFeatureValidation,

  normalizeFeatureMetadata,

  normalizeFeatureResponse,

  createEmptyWorkspaceFilters,

  normalizeWorkspaceFilterDate,

  normalizeWorkspaceFilters,

  hasActiveWorkspaceFilters,

  normalizeFeatureListItem,

  createEmptyPagination,

  normalizePagination,

  normalizeWorkspaceResponseFilters,

  normalizeFeatureListResponse,

  normalizeFeatureSelectionResponse,

  createEmptyFeatureSummary,

  normalizeFeatureSummary,

  buildExtractionRequest,

  createFeatureExtractionRequest,

  buildBatchExtractionRequest,

  createBatchExtractionRequest,

  normalizeExtractionSummary,

  normalizeExtractionResponse,

  normalizeFeatureHealth,

  normalizeDefinition,

  normalizeDefinitionsResponse,

  normalizeFeatureDefinitions,

  getFeatureStatusLabel,

  getFeatureSourceLabel,

  getFeatureLevelLabel,

  isFeatureReady,

  isFeaturePending,

  isFeatureFailed,

  isFeatureSelectable,

  getSelectableFeatureIds,

  getPendingFeatureIds,

  getFailedFeatureIds,

  getWarningFeatureIds,

  normalizeSelectedIds,

  toggleSelectedId,

  areAllIdsSelected,

  selectAllIds,

  removeIds,

  clearSelectedIds,

  createEmptySelectionState,

  normalizeSelectionState,

  isGlobalSelectionComplete,

  createEmptyFeatureDetails,

  hasFeatureDetails,
};
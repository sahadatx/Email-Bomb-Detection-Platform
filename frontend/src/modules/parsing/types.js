/**
 * ============================================================================
 * Email Parsing & Normalization
 * Module 03
 * ============================================================================
 *
 * Frontend data contracts for the parsing module.
 *
 * Module ownership
 * ----------------
 *
 * Module 02:
 *     - source
 *     - source_identifier
 *     - ground_truth level
 *     - received_at
 *     - original collected email
 *
 * Module 03:
 *     - parsing status
 *     - parsed identity
 *     - parsed headers
 *     - parsed body
 *     - MIME structure
 *     - attachments
 *     - validation results
 *
 * IMPORTANT
 * ---------
 * `level` and `parsing_status` are different concepts.
 *
 * Level:
 *     NORMAL / BOMBING
 *
 * Parsing status:
 *     PENDING / PARSED / WARNING / FAILED
 *
 * Module 03 does not perform:
 *     - ML classification
 *     - prediction
 *     - confidence scoring
 *     - risk scoring
 *     - threat scoring
 * ============================================================================
 */


// ============================================================================
// Constants
// ============================================================================

export const DEFAULT_PAGE = 1;

export const DEFAULT_PAGE_SIZE = 30;

export const MAX_PAGE_SIZE = 100;


// ============================================================================
// Parsing Status
// ============================================================================

/**
 * Public/UI parsing status values.
 *
 * PENDING
 *     Source email exists in Module 02 but no ParsedEmail
 *     persistence record exists yet.
 *
 * PARSED
 *     Parsing completed successfully.
 *
 * WARNING
 *     Parsing completed with non-fatal validation warnings.
 *
 * FAILED
 *     Parsing or validation produced fatal errors.
 */
export const PARSING_STATUS = Object.freeze({
  PENDING: "pending",
  PARSED: "parsed",
  WARNING: "warning",
  FAILED: "failed",
});


// ============================================================================
// Parsing Status Options
// ============================================================================

export const PARSING_STATUS_OPTIONS =
  Object.freeze([
    {
      value: "",
      label: "All Status",
    },
    {
      value: PARSING_STATUS.PENDING,
      label: "Pending",
    },
    {
      value: PARSING_STATUS.PARSED,
      label: "Parsed",
    },
    {
      value: PARSING_STATUS.WARNING,
      label: "Warning",
    },
    {
      value: PARSING_STATUS.FAILED,
      label: "Failed",
    },
  ]);


// ============================================================================
// Ground Truth Level
// ============================================================================

/**
 * Ground-truth label owned by Module 02.
 *
 * This is displayed as "Level" in the Module 03 UI.
 *
 * It is NOT a prediction.
 */
export const EMAIL_LEVEL = Object.freeze({
  NORMAL: "normal",
  BOMBING: "bombing",
});


// ============================================================================
// Ground Truth Level Options
// ============================================================================

export const EMAIL_LEVEL_OPTIONS =
  Object.freeze([
    {
      value: "",
      label: "All Level",
    },
    {
      value: EMAIL_LEVEL.NORMAL,
      label: "Normal",
    },
    {
      value: EMAIL_LEVEL.BOMBING,
      label: "Bombing",
    },
  ]);


// ============================================================================
// Email Source
// ============================================================================

/**
 * Source values owned by Module 02.
 */
export const EMAIL_SOURCE = Object.freeze({
  RAW_EMAIL: "raw_email",
  FILE_UPLOAD: "file_upload",

  /**
   * Legacy backend source.
   *
   * Kept for compatibility with existing records/API contracts.
   * It is not required by the new Module 02 UI.
   */
  IMAP: "imap",
});


// ============================================================================
// Email Source Options
// ============================================================================

export const EMAIL_SOURCE_OPTIONS =
  Object.freeze([
    {
      value: "",
      label: "All Source",
    },
    {
      value: EMAIL_SOURCE.FILE_UPLOAD,
      label: "File Upload",
    },
    {
      value: EMAIL_SOURCE.RAW_EMAIL,
      label: "Raw Email",
    },
  ]);


// ============================================================================
// Module 02 Email Status
// ============================================================================

/**
 * These values belong to Module 02 EmailStatus.
 *
 * IMPORTANT
 * ---------
 * This is NOT the Status displayed in the Module 03 parsing
 * workspace table.
 *
 * Module 03 table Status = PARSING_STATUS.
 *
 * This constant remains available only for compatibility with
 * canonical Module 02 email metadata when required.
 */
export const EMAIL_STATUS = Object.freeze({
  INGESTED: "ingested",
  FAILED: "failed",
});


// ============================================================================
// Parsing Workspace Filters
// ============================================================================

/**
 * Final Parsing Workspace filter layout:
 *
 *     Search
 *     Source
 *     Level
 *     Status
 *     From
 *     To
 *     Reset Filters
 *
 * Different filter fields use AND semantics.
 *
 * Search fields use OR semantics inside the backend:
 *
 *     Subject
 *     Sender
 *     Message-ID
 *     Source Identifier
 */
export const EMPTY_PARSING_FILTERS =
  Object.freeze({
    search: "",
    source: "",
    level: "",
    status: "",
    from_date: "",
    to_date: "",
  });


// ============================================================================
// Parsing Filter Keys
// ============================================================================

export const PARSING_FILTER_KEYS =
  Object.freeze({
    SEARCH: "search",
    SOURCE: "source",
    LEVEL: "level",
    STATUS: "status",
    FROM_DATE: "from_date",
    TO_DATE: "to_date",
  });


// ============================================================================
// Parsed Email Identity
// ============================================================================

/**
 * @typedef {Object} ParsedEmailIdentity
 *
 * @property {string|null} message_id
 * @property {string|null} subject
 * @property {string|null} sender
 * @property {string[]} recipients
 * @property {string[]} reply_to
 * @property {string[]} cc
 * @property {string[]} bcc
 * @property {string|null} date
 */


// ============================================================================
// Parsed Email Timestamps
// ============================================================================

/**
 * @typedef {Object} ParsedEmailTimestamps
 *
 * @property {string|null} received_at
 * @property {string} collected_at
 * @property {string|null} parsed_at
 */


// ============================================================================
// Parsing Metadata
// ============================================================================

/**
 * @typedef {Object} ParsingMetadata
 *
 * @property {string} status
 * @property {string|null} parser_version
 * @property {number|null} processing_time_ms
 */


// ============================================================================
// MIME Part
// ============================================================================

/**
 * @typedef {Object} ParsedMimePart
 *
 * @property {string} content_type
 * @property {string|null} content_disposition
 * @property {string|null} charset
 * @property {string|null} filename
 * @property {number} size
 */


// ============================================================================
// Attachment
// ============================================================================

/**
 * @typedef {Object} ParsedAttachment
 *
 * @property {string|null} filename
 * @property {string} content_type
 * @property {string|null} content_disposition
 * @property {number} size
 * @property {string|null} content_id
 */


// ============================================================================
// Validation
// ============================================================================

/**
 * @typedef {Object} ValidationResult
 *
 * @property {string[]} errors
 * @property {string[]} warnings
 * @property {boolean} is_valid
 */


// ============================================================================
// Full Parsed Email Response
// ============================================================================

/**
 * @typedef {Object} ParsedEmailResponse
 *
 * @property {string} email_id
 *
 * Module 02 canonical metadata:
 *
 * @property {string} source
 * @property {string|null} source_identifier
 * @property {string} level
 *
 * Parsed identity:
 *
 * @property {ParsedEmailIdentity} identity
 * @property {ParsedEmailTimestamps} timestamps
 * @property {ParsingMetadata} parsing
 *
 * Parsed structures:
 *
 * @property {Object<string, string[]>} headers
 * @property {string|null} text_body
 * @property {string|null} html_body
 * @property {ParsedMimePart[]} mime_parts
 * @property {ParsedAttachment[]} attachments
 *
 * Validation:
 *
 * @property {string[]} validation_errors
 * @property {string[]} validation_warnings
 *
 * IMPORTANT:
 *
 * `level`
 *     Ground truth from Module 02.
 *
 * `parsing.status`
 *     Module 03 parsing status.
 *
 * `raw_content`
 *     Intentionally NOT part of this response.
 *
 * Module 02 remains the canonical source for raw email content.
 */


// ============================================================================
// Parsing Email List Item
// ============================================================================

/**
 * @typedef {Object} ParsingEmailListItem
 *
 * Final Parsing Workspace table:
 *
 *     Subject
 *     Sender
 *     Source
 *     Level
 *     Received
 *     Status
 *     Action
 *
 * @property {string} email_id
 * @property {string} source
 * @property {string|null} source_identifier
 * @property {string} level
 * @property {string|null} message_id
 * @property {string|null} sender
 * @property {string|null} subject
 * @property {string|null} received_at
 * @property {string} collected_at
 * @property {string} parsing_status
 *
 * NOTE:
 *
 * There is intentionally no generic `status` property here.
 *
 * The table Status represents Module 03 parsing status:
 *
 *     pending
 *     parsed
 *     warning
 *     failed
 */


// ============================================================================
// Pagination
// ============================================================================

/**
 * @typedef {Object} ParsingPagination
 *
 * @property {number} page
 * @property {number} page_size
 * @property {number} total
 * @property {number} total_pages
 * @property {number} start_index
 * @property {number} end_index
 */


// ============================================================================
// Parsing Email List Response
// ============================================================================

/**
 * @typedef {Object} ParsingEmailListResponse
 *
 * Backend response:
 *
 * {
 *     items,
 *     total,
 *     page,
 *     page_size,
 *     total_pages,
 *     start_index,
 *     end_index
 * }
 *
 * There is no nested `pagination` property.
 *
 * @property {ParsingEmailListItem[]} items
 * @property {number} total
 * @property {number} page
 * @property {number} page_size
 * @property {number} total_pages
 * @property {number} start_index
 * @property {number} end_index
 */


// ============================================================================
// Parse Email Request
// ============================================================================

/**
 * @typedef {Object} ParseEmailRequest
 *
 * @property {string} email_id
 */


// ============================================================================
// Batch Parse Request
// ============================================================================

/**
 * @typedef {Object} ParseEmailsRequest
 *
 * @property {string[]} email_ids
 *
 * Maximum:
 *
 *     100 email IDs per request
 */


// ============================================================================
// Parse Matching Request
// ============================================================================

/**
 * @typedef {Object} ParseMatchingEmailsRequest
 *
 * @property {string|null} search
 * @property {string|null} source
 * @property {string|null} level
 * @property {string|null} status
 * @property {string|null} from_date
 * @property {string|null} to_date
 *
 * Pagination is intentionally NOT included.
 *
 * The request represents all emails matching the filters,
 * not only the current UI page.
 */


// ============================================================================
// Parse All Pending Request
// ============================================================================

/**
 * @typedef {Object} ParseAllPendingRequest
 *
 * @property {boolean} confirm
 *
 * Backend requires explicit confirmation.
 */


// ============================================================================
// Matching Email IDs Response
// ============================================================================

/**
 * @typedef {string[]} MatchingEmailIdsResponse
 *
 * Used by:
 *
 *     Select All Matching
 *
 * This response is not paginated.
 */


// ============================================================================
// Batch Parsing Response
// ============================================================================

/**
 * The explicit batch parsing endpoint returns:
 *
 *     ParsedEmailResponse[]
 *
 * Therefore:
 *
 * @typedef {ParsedEmailResponse[]} BatchParsingResponse
 */


// ============================================================================
// Parsing Summary
// ============================================================================

/**
 * Operation-level summary.
 *
 * This represents one parsing operation.
 *
 * It is NOT the global Module 03 database state.
 *
 * @typedef {Object} ParsingSummary
 *
 * @property {number} selected
 * @property {number} parsed
 * @property {number} warnings
 * @property {number} failed
 */


// ============================================================================
// Global Parsing Persistence Summary
// ============================================================================

/**
 * Global Module 03 parsing state.
 *
 * @typedef {Object} ParsingPersistenceSummary
 *
 * @property {number} total_collected
 * @property {number} total_parsed
 * @property {number} total_pending
 * @property {number} total_warnings
 * @property {number} total_failed
 * @property {number} ready_for_features
 * @property {number} readiness_percentage
 */


// ============================================================================
// Global Parsing Summary Response
// ============================================================================

/**
 * Public API representation of the global Module 03 summary.
 *
 * Backend:
 *
 *     GET /parsing/summary
 *
 * @typedef {Object} ParsingSummaryResponse
 *
 * @property {number} total_collected
 * @property {number} parsed
 * @property {number} pending
 * @property {number} warnings
 * @property {number} failed
 * @property {number} ready_for_features
 * @property {number} readiness_percentage
 */


// ============================================================================
// Table Configuration
// ============================================================================

/**
 * Canonical Parsing Workspace table columns.
 *
 * Action is intentionally separate from the email data itself.
 *
 * Action:
 *
 *     View
 */
export const PARSING_TABLE_COLUMNS =
  Object.freeze([
    {
      key: "subject",
      label: "Subject",
    },
    {
      key: "sender",
      label: "Sender",
    },
    {
      key: "source",
      label: "Source",
    },
    {
      key: "level",
      label: "Level",
    },
    {
      key: "received_at",
      label: "Received",
    },
    {
      key: "parsing_status",
      label: "Status",
    },
    {
      key: "action",
      label: "Action",
    },
  ]);


// ============================================================================
// Parsing Actions
// ============================================================================

export const PARSING_ACTIONS =
  Object.freeze({
    VIEW: "view",
    SELECT_ALL_MATCHING: "select_all_matching",
    CLEAR_SELECTION: "clear_selection",
    PARSE_SELECTED: "parse_selected",
    PARSE_ALL_PENDING: "parse_all_pending",
  });


// ============================================================================
// UI Helpers
// ============================================================================

export const isParsingSuccessful = (
  status,
) =>
  status ===
  PARSING_STATUS.PARSED;


export const isParsingWarning = (
  status,
) =>
  status ===
  PARSING_STATUS.WARNING;


export const isParsingFailed = (
  status,
) =>
  status ===
  PARSING_STATUS.FAILED;


export const isParsingPending = (
  status,
) =>
  status ===
  PARSING_STATUS.PENDING;


// ============================================================================
// Level Helpers
// ============================================================================

export const isNormalLevel = (
  level,
) =>
  level ===
  EMAIL_LEVEL.NORMAL;


export const isBombingLevel = (
  level,
) =>
  level ===
  EMAIL_LEVEL.BOMBING;


export function isKnownEmailLevel(
  level,
) {
  return (
    level ===
      EMAIL_LEVEL.NORMAL ||
    level ===
      EMAIL_LEVEL.BOMBING
  );
}


export function normalizeEmailLevel(
  level,
) {
  if (
    isKnownEmailLevel(level)
  ) {
    return level;
  }

  return EMAIL_LEVEL.NORMAL;
}


// ============================================================================
// Source Helpers
// ============================================================================

export function isKnownEmailSource(
  source,
) {
  return (
    source ===
      EMAIL_SOURCE.RAW_EMAIL ||
    source ===
      EMAIL_SOURCE.FILE_UPLOAD ||
    source ===
      EMAIL_SOURCE.IMAP
  );
}


export function normalizeEmailSource(
  source,
) {
  if (
    isKnownEmailSource(source)
  ) {
    return source;
  }

  return EMAIL_SOURCE.RAW_EMAIL;
}


// ============================================================================
// Status Helpers
// ============================================================================

export function isKnownParsingStatus(
  status,
) {
  return (
    status ===
      PARSING_STATUS.PENDING ||
    status ===
      PARSING_STATUS.PARSED ||
    status ===
      PARSING_STATUS.WARNING ||
    status ===
      PARSING_STATUS.FAILED
  );
}


export function normalizeParsingStatus(
  status,
) {
  if (
    isKnownParsingStatus(status)
  ) {
    return status;
  }

  return PARSING_STATUS.PENDING;
}


// ============================================================================
// List Item Status Helper
// ============================================================================

export function getParsingStatusFromListItem(
  item,
) {
  if (!item) {
    return PARSING_STATUS.PENDING;
  }

  return normalizeParsingStatus(
    item.parsing_status,
  );
}


// ============================================================================
// Filter Helpers
// ============================================================================

export function createEmptyParsingFilters() {
  return {
    search: "",
    source: "",
    level: "",
    status: "",
    from_date: "",
    to_date: "",
  };
}


export function normalizeParsingFilters(
  filters,
) {
  const source =
    filters?.source ?? "";

  const level =
    filters?.level ?? "";

  const status =
    filters?.status ?? "";

  return {
    search:
      typeof filters?.search === "string"
        ? filters.search.trim()
        : "",

    source:
      isKnownEmailSource(source)
        ? source
        : "",

    level:
      isKnownEmailLevel(level)
        ? level
        : "",

    status:
      isKnownParsingStatus(status)
        ? status
        : "",

    from_date:
      typeof filters?.from_date === "string"
        ? filters.from_date
        : "",

    to_date:
      typeof filters?.to_date === "string"
        ? filters.to_date
        : "",
  };
}


export function hasActiveParsingFilters(
  filters,
) {
  const normalized =
    normalizeParsingFilters(
      filters,
    );

  return Boolean(
    normalized.search ||
    normalized.source ||
    normalized.level ||
    normalized.status ||
    normalized.from_date ||
    normalized.to_date,
  );
}


// ============================================================================
// Pagination Helpers
// ============================================================================

export function normalizePage(
  page,
) {
  const value = Number(page);

  if (
    !Number.isFinite(value) ||
    value < 1
  ) {
    return DEFAULT_PAGE;
  }

  return Math.floor(value);
}


export function normalizePageSize(
  pageSize,
) {
  const value = Number(
    pageSize,
  );

  if (
    !Number.isFinite(value) ||
    value < 1
  ) {
    return DEFAULT_PAGE_SIZE;
  }

  return Math.min(
    MAX_PAGE_SIZE,
    Math.floor(value),
  );
}


export function normalizePagination(
  pagination,
) {
  return {
    page: normalizePage(
      pagination?.page,
    ),

    page_size: normalizePageSize(
      pagination?.page_size,
    ),

    total:
      Number.isFinite(
        Number(
          pagination?.total,
        ),
      )
        ? Math.max(
            0,
            Number(
              pagination.total,
            ),
          )
        : 0,

    total_pages:
      Number.isFinite(
        Number(
          pagination?.total_pages,
        ),
      )
        ? Math.max(
            1,
            Number(
              pagination.total_pages,
            ),
          )
        : 1,

    start_index:
      Number.isFinite(
        Number(
          pagination?.start_index,
        ),
      )
        ? Math.max(
            0,
            Number(
              pagination.start_index,
            ),
          )
        : 0,

    end_index:
      Number.isFinite(
        Number(
          pagination?.end_index,
        ),
      )
        ? Math.max(
            0,
            Number(
              pagination.end_index,
            ),
          )
        : 0,
  };
}


// ============================================================================
// Summary Helpers
// ============================================================================

export function isReadyForFeatures(
  summary,
) {
  if (!summary) {
    return false;
  }

  return (
    Number(
      summary.ready_for_features,
    ) > 0
  );
}


export function getParsingReadinessPercentage(
  summary,
) {
  if (!summary) {
    return 0;
  }

  const value = Number(
    summary.readiness_percentage,
  );

  if (
    !Number.isFinite(value)
  ) {
    return 0;
  }

  return Math.max(
    0,
    Math.min(
      100,
      value,
    ),
  );
}


export function getTotalCollected(
  summary,
) {
  if (!summary) {
    return 0;
  }

  const value = Number(
    summary.total_collected,
  );

  return Number.isFinite(value)
    ? Math.max(
        0,
        value,
      )
    : 0;
}


export function getTotalParsed(
  summary,
) {
  if (!summary) {
    return 0;
  }

  const value = Number(
    summary.total_parsed ??
      summary.parsed,
  );

  return Number.isFinite(value)
    ? Math.max(
        0,
        value,
      )
    : 0;
}


export function getTotalPending(
  summary,
) {
  if (!summary) {
    return 0;
  }

  const value = Number(
    summary.total_pending ??
      summary.pending,
  );

  return Number.isFinite(value)
    ? Math.max(
        0,
        value,
      )
    : 0;
}


export function getTotalWarnings(
  summary,
) {
  if (!summary) {
    return 0;
  }

  const value = Number(
    summary.total_warnings ??
      summary.warnings,
  );

  return Number.isFinite(value)
    ? Math.max(
        0,
        value,
      )
    : 0;
}


export function getTotalFailed(
  summary,
) {
  if (!summary) {
    return 0;
  }

  const value = Number(
    summary.total_failed ??
      summary.failed,
  );

  return Number.isFinite(value)
    ? Math.max(
        0,
        value,
      )
    : 0;
}


// ============================================================================
// Safe Collection Helpers
// ============================================================================

export function normalizeStringArray(
  value,
) {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter(
      (item) =>
        item !== null &&
        item !== undefined,
    )
    .map(
      (item) =>
        String(item),
    );
}


export function normalizeObject(
  value,
) {
  if (
    value === null ||
    typeof value !== "object" ||
    Array.isArray(value)
  ) {
    return {};
  }

  return value;
}


// ============================================================================
// Parsed Email Normalization
// ============================================================================

export function normalizeParsedEmailIdentity(
  identity,
) {
  if (
    !identity ||
    typeof identity !== "object"
  ) {
    return {
      message_id: null,
      subject: null,
      sender: null,
      recipients: [],
      reply_to: [],
      cc: [],
      bcc: [],
      date: null,
    };
  }

  return {
    message_id:
      identity.message_id ?? null,

    subject:
      identity.subject ?? null,

    sender:
      identity.sender ?? null,

    recipients:
      normalizeStringArray(
        identity.recipients,
      ),

    reply_to:
      normalizeStringArray(
        identity.reply_to,
      ),

    cc:
      normalizeStringArray(
        identity.cc,
      ),

    bcc:
      normalizeStringArray(
        identity.bcc,
      ),

    date:
      identity.date ?? null,
  };
}


export function normalizeParsingMetadata(
  parsing,
) {
  if (
    !parsing ||
    typeof parsing !== "object"
  ) {
    return {
      status:
        PARSING_STATUS.PENDING,
      parser_version: null,
      processing_time_ms: null,
    };
  }

  const processingTime =
    Number(
      parsing.processing_time_ms,
    );

  return {
    status:
      normalizeParsingStatus(
        parsing.status,
      ),

    parser_version:
      parsing.parser_version ??
      null,

    processing_time_ms:
      Number.isFinite(
        processingTime,
      )
        ? processingTime
        : null,
  };
}


export function normalizeParsedEmail(
  email,
) {
  if (
    !email ||
    typeof email !== "object"
  ) {
    return null;
  }

  return {
    email_id:
      email.email_id ?? null,

    source:
      normalizeEmailSource(
        email.source,
      ),

    source_identifier:
      email.source_identifier ??
      null,

    level:
      normalizeEmailLevel(
        email.level,
      ),

    identity:
      normalizeParsedEmailIdentity(
        email.identity,
      ),

    timestamps: {
      received_at:
        email.timestamps
          ?.received_at ?? null,

      collected_at:
        email.timestamps
          ?.collected_at ?? null,

      parsed_at:
        email.timestamps
          ?.parsed_at ?? null,
    },

    parsing:
      normalizeParsingMetadata(
        email.parsing,
      ),

    headers:
      normalizeObject(
        email.headers,
      ),

    text_body:
      email.text_body ?? null,

    html_body:
      email.html_body ?? null,

    mime_parts:
      Array.isArray(
        email.mime_parts,
      )
        ? email.mime_parts
        : [],

    attachments:
      Array.isArray(
        email.attachments,
      )
        ? email.attachments
        : [],

    validation_errors:
      normalizeStringArray(
        email.validation_errors,
      ),

    validation_warnings:
      normalizeStringArray(
        email.validation_warnings,
      ),
  };
}


// ============================================================================
// Validation Helpers
// ============================================================================

export function buildValidationResult(
  email,
) {
  const errors =
    normalizeStringArray(
      email?.validation_errors,
    );

  const warnings =
    normalizeStringArray(
      email?.validation_warnings,
    );

  return {
    errors,
    warnings,
    is_valid:
      errors.length === 0,
  };
}


// ============================================================================
// Default / Safe Values
// ============================================================================

export const EMPTY_PARSING_IDENTITY =
  Object.freeze({
    message_id: null,
    subject: null,
    sender: null,
    recipients: [],
    reply_to: [],
    cc: [],
    bcc: [],
    date: null,
  });


export const EMPTY_PARSING_TIMESTAMPS =
  Object.freeze({
    received_at: null,
    collected_at: null,
    parsed_at: null,
  });


export const EMPTY_PARSING_METADATA =
  Object.freeze({
    status:
      PARSING_STATUS.PENDING,

    parser_version: null,

    processing_time_ms: null,
  });


export const EMPTY_VALIDATION_RESULT =
  Object.freeze({
    errors: [],
    warnings: [],
    is_valid: true,
  });


export const EMPTY_PAGINATION =
  Object.freeze({
    page: DEFAULT_PAGE,
    page_size:
      DEFAULT_PAGE_SIZE,
    total: 0,
    total_pages: 1,
    start_index: 0,
    end_index: 0,
  });


// ============================================================================
// Empty Global Parsing Summary
// ============================================================================

export const EMPTY_PARSING_SUMMARY =
  Object.freeze({
    selected: 0,
    parsed: 0,
    warnings: 0,
    failed: 0,
  });


export const EMPTY_PERSISTENCE_SUMMARY =
  Object.freeze({
    total_collected: 0,
    total_parsed: 0,
    total_pending: 0,
    total_warnings: 0,
    total_failed: 0,
    ready_for_features: 0,
    readiness_percentage: 0,
  });


// ============================================================================
// Empty API Response
// ============================================================================

export const EMPTY_PARSING_LIST_RESPONSE =
  Object.freeze({
    items: [],
    total: 0,
    page: DEFAULT_PAGE,
    page_size:
      DEFAULT_PAGE_SIZE,
    total_pages: 1,
    start_index: 0,
    end_index: 0,
  });
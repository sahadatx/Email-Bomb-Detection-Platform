import apiClient from "../../../core/api/client";

import {
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
  MAX_PAGE_SIZE,
  EMAIL_LEVEL,
  EMAIL_SOURCE,
  PARSING_STATUS,
  normalizeParsingFilters,
} from "../types";


// ============================================================================
// API CONFIGURATION
// ============================================================================

const API_PREFIX = "/parsing";


// ============================================================================
// NORMALIZATION HELPERS
// ============================================================================

function normalizePage(page) {
  const value = Number(page);

  if (!Number.isFinite(value)) {
    return DEFAULT_PAGE;
  }

  return Math.max(
    1,
    Math.trunc(value),
  );
}


function normalizePageSize(pageSize) {
  const value = Number(pageSize);

  if (!Number.isFinite(value)) {
    return DEFAULT_PAGE_SIZE;
  }

  return Math.min(
    MAX_PAGE_SIZE,
    Math.max(
      1,
      Math.trunc(value),
    ),
  );
}


function normalizeEmailId(emailId) {
  if (
    emailId === null ||
    emailId === undefined
  ) {
    return null;
  }

  const value =
    String(emailId).trim();

  return value || null;
}


function normalizeEmailIds(emailIds) {
  if (!Array.isArray(emailIds)) {
    return [];
  }

  return [
    ...new Set(
      emailIds
        .map(normalizeEmailId)
        .filter(Boolean),
    ),
  ];
}


function normalizeOptionalString(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "";
  }

  return String(value).trim();
}


// ============================================================================
// FILTER NORMALIZATION
// ============================================================================

function normalizeFilters(filters = {}) {
  return normalizeParsingFilters(
    filters,
  );
}


// ============================================================================
// QUERY PARAMETER BUILDER
// ============================================================================

function buildQueryParams({
  page = DEFAULT_PAGE,
  pageSize = DEFAULT_PAGE_SIZE,
  search = "",
  source = "",
  level = "",
  status = "",
  fromDate = "",
  toDate = "",
} = {}) {
  const params =
    new URLSearchParams();

  params.set(
    "page",
    String(
      normalizePage(page),
    ),
  );

  params.set(
    "page_size",
    String(
      normalizePageSize(
        pageSize,
      ),
    ),
  );

  const normalizedSearch =
    normalizeOptionalString(
      search,
    );

  const normalizedSource =
    normalizeOptionalString(
      source,
    );

  const normalizedLevel =
    normalizeOptionalString(
      level,
    );

  const normalizedStatus =
    normalizeOptionalString(
      status,
    );

  const normalizedFromDate =
    normalizeOptionalString(
      fromDate,
    );

  const normalizedToDate =
    normalizeOptionalString(
      toDate,
    );

  if (normalizedSearch) {
    params.set(
      "search",
      normalizedSearch,
    );
  }

  if (normalizedSource) {
    params.set(
      "source",
      normalizedSource,
    );
  }

  if (normalizedLevel) {
    params.set(
      "level",
      normalizedLevel,
    );
  }

  if (normalizedStatus) {
    params.set(
      "status",
      normalizedStatus,
    );
  }

  if (normalizedFromDate) {
    params.set(
      "from_date",
      normalizedFromDate,
    );
  }

  if (normalizedToDate) {
    params.set(
      "to_date",
      normalizedToDate,
    );
  }

  return params.toString();
}


// ============================================================================
// FILTER QUERY BUILDER
// ============================================================================

function buildFilterQueryParams(
  filters = {},
) {
  const normalized =
    normalizeFilters(
      filters,
    );

  return {
    search:
      normalized.search,

    source:
      normalized.source,

    level:
      normalized.level,

    status:
      normalized.status,

    fromDate:
      normalized.from_date,

    toDate:
      normalized.to_date,
  };
}


// ============================================================================
// HEALTH
// ============================================================================

export async function getParsingHealth(
  { signal } = {},
) {
  const response =
    await apiClient.get(
      `${API_PREFIX}/health`,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// GLOBAL PARSING SUMMARY
// ============================================================================

export async function getParsingSummary(
  { signal } = {},
) {
  const response =
    await apiClient.get(
      `${API_PREFIX}/summary`,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// LIST PARSING WORKSPACE EMAILS
// ============================================================================

/**
 * Retrieve the Module 03 Parsing Workspace.
 *
 * Supported filters:
 *
 *     Search
 *     Source
 *     Level
 *     Status
 *     From
 *     To
 *
 * Pagination is independent from parsing batch size.
 *
 * UI page size:
 *
 *     30
 *
 * Maximum API page size:
 *
 *     100
 *
 * IMPORTANT:
 *
 * This endpoint only controls what is displayed in the workspace.
 *
 * It does NOT limit the number of emails that can be selected
 * through "Select All Matching" or parsed through
 * "Parse All Pending".
 */
export async function getParsingEmails({
  page = DEFAULT_PAGE,
  pageSize = DEFAULT_PAGE_SIZE,
  filters = {},
  signal,
} = {}) {
  const normalizedFilters =
    buildFilterQueryParams(
      filters,
    );

  const query =
    buildQueryParams({
      page,
      pageSize,
      ...normalizedFilters,
    });

  const response =
    await apiClient.get(
      `${API_PREFIX}/emails?${query}`,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// GET MATCHING EMAIL IDS
// ============================================================================

/**
 * Retrieve all email IDs matching the current workspace filters.
 *
 * This endpoint is used by:
 *
 *     Select All Matching
 *
 * IMPORTANT:
 *
 * This is intentionally NOT paginated.
 *
 * The current UI page may contain only 30 emails while the
 * matching result may contain thousands.
 */
export async function getMatchingEmailIds({
  filters = {},
  signal,
} = {}) {
  const normalizedFilters =
    buildFilterQueryParams(
      filters,
    );

  const query =
    buildQueryParams({
      page:
        DEFAULT_PAGE,

      pageSize:
        DEFAULT_PAGE_SIZE,

      ...normalizedFilters,
    });

  const params =
    new URLSearchParams(
      query,
    );

  params.delete(
    "page",
  );

  params.delete(
    "page_size",
  );

  const finalQuery =
    params.toString();

  const response =
    await apiClient.get(
      `${API_PREFIX}/emails/matching/ids${
        finalQuery
          ? `?${finalQuery}`
          : ""
      }`,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// GET PENDING EMAIL IDS
// ============================================================================

/**
 * Retrieve all currently pending email IDs.
 *
 * Used by:
 *
 *     Parse All Pending
 *
 * This is intentionally NOT paginated.
 */
export async function getPendingEmailIds({
  signal,
} = {}) {
  const response =
    await apiClient.get(
      `${API_PREFIX}/emails/pending/ids`,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// GET PERSISTED PARSED EMAIL
// ============================================================================

export async function getParsedEmail(
  emailId,
  { signal } = {},
) {
  const normalizedEmailId =
    normalizeEmailId(
      emailId,
    );

  if (!normalizedEmailId) {
    throw new Error(
      "emailId is required to retrieve a parsed email.",
    );
  }

  const response =
    await apiClient.get(
      `${API_PREFIX}/emails/${encodeURIComponent(
        normalizedEmailId,
      )}`,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// PARSE SINGLE EMAIL
// ============================================================================

export async function parseEmail(
  emailId,
  { signal } = {},
) {
  const normalizedEmailId =
    normalizeEmailId(
      emailId,
    );

  if (!normalizedEmailId) {
    throw new Error(
      "emailId is required to parse an email.",
    );
  }

  const response =
    await apiClient.post(
      `${API_PREFIX}/emails/${encodeURIComponent(
        normalizedEmailId,
      )}/parse`,
      undefined,
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// PARSE MULTIPLE EMAILS
// ============================================================================

/**
 * Parse an explicit list of email IDs.
 *
 * Backend contract:
 *
 *     maximum 100 IDs per request.
 *
 * This method intentionally does not automatically split
 * the request. The caller should use the higher-level
 * batch workflow when parsing thousands of emails.
 */
export async function parseEmails(
  emailIds,
  { signal } = {},
) {
  if (!Array.isArray(emailIds)) {
    throw new TypeError(
      "emailIds must be an array.",
    );
  }

  const normalizedIds =
    normalizeEmailIds(
      emailIds,
    );

  if (
    normalizedIds.length ===
    0
  ) {
    throw new Error(
      "At least one valid email ID is required for batch parsing.",
    );
  }

  if (
    normalizedIds.length >
    MAX_PAGE_SIZE
  ) {
    throw new Error(
      `A maximum of ${MAX_PAGE_SIZE} emails can be parsed in one batch.`,
    );
  }

  const response =
    await apiClient.post(
      `${API_PREFIX}/emails/parse`,
      {
        email_ids:
          normalizedIds,
      },
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// PARSE EMAILS MATCHING CURRENT FILTERS
// ============================================================================

/**
 * Parse all emails matching the supplied filters.
 *
 * This operation is different from `parseEmails()`.
 *
 * parseEmails()
 *     explicit email IDs
 *
 * parseMatchingEmails()
 *     filter-driven selection across the complete result set
 *
 * Example:
 *
 *     Level = BOMBING
 *     Status = Pending
 *
 * will parse all pending bombing emails matching those filters,
 * not only the 30 visible rows.
 */
export async function parseMatchingEmails({
  filters = {},
  signal,
} = {}) {
  const normalizedFilters =
    normalizeFilters(
      filters,
    );

  const response =
    await apiClient.post(
      `${API_PREFIX}/emails/parse/matching`,
      {
        search:
          normalizedFilters.search ||
          null,

        source:
          normalizedFilters.source ||
          null,

        level:
          normalizedFilters.level ||
          null,

        status:
          normalizedFilters.status ||
          null,

        from_date:
          normalizedFilters.from_date ||
          null,

        to_date:
          normalizedFilters.to_date ||
          null,
      },
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// PARSE ALL PENDING EMAILS
// ============================================================================

/**
 * Parse every currently pending email.
 *
 * Backend requires explicit confirmation.
 */
export async function parseAllPending({
  confirm = true,
  signal,
} = {}) {
  if (confirm !== true) {
    throw new Error(
      "Parsing all pending emails requires explicit confirmation.",
    );
  }

  const response =
    await apiClient.post(
      `${API_PREFIX}/emails/parse/pending`,
      {
        confirm: true,
      },
      {
        signal,
      },
    );

  return response.data;
}


// ============================================================================
// PARSE SELECTED EMAILS
// ============================================================================

/**
 * Semantic alias for the UI action:
 *
 *     Parse Selected
 *
 * The actual API operation is the explicit batch parser.
 */
export async function parseSelectedEmails(
  emailIds,
  { signal } = {},
) {
  return parseEmails(
    emailIds,
    {
      signal,
    },
  );
}


// ============================================================================
// SELECT ALL MATCHING
// ============================================================================

/**
 * Semantic helper for the UI:
 *
 *     Select All Matching
 *
 * Returns every matching email ID across all pages.
 */
export async function selectAllMatchingEmails({
  filters = {},
  signal,
} = {}) {
  return getMatchingEmailIds({
    filters,
    signal,
  });
}


// ============================================================================
// NORMALIZE BATCH RESULT
// ============================================================================

/**
 * The backend currently returns:
 *
 *     list[ParsedEmailResponse]
 *
 * This helper makes the frontend resilient to an empty/invalid
 * response without changing the backend contract.
 */
export function normalizeBatchParsingResponse(
  response,
) {
  if (!Array.isArray(response)) {
    return [];
  }

  return response;
}


// ============================================================================
// SERVICE ERROR HELPERS
// ============================================================================

/**
 * Extract a user-facing message from the API error object.
 *
 * This function does not hide the original error.
 * It only provides a consistent message for UI components.
 */
export function getParsingServiceErrorMessage(
  error,
) {
  if (!error) {
    return "An unknown parsing error occurred.";
  }

  if (
    typeof error.message ===
    "string" &&
    error.message.trim()
  ) {
    return error.message.trim();
  }

  const responseData =
    error?.response?.data;

  if (
    typeof responseData ===
    "string" &&
    responseData.trim()
  ) {
    return responseData.trim();
  }

  if (
    responseData &&
    typeof responseData ===
      "object"
  ) {
    if (
      typeof responseData.detail ===
        "string" &&
      responseData.detail.trim()
    ) {
      return responseData.detail.trim();
    }

    if (
      typeof responseData.message ===
        "string" &&
      responseData.message.trim()
    ) {
      return responseData.message.trim();
    }

    if (
      Array.isArray(
        responseData.detail,
      )
    ) {
      return responseData.detail
        .map(
          (item) => {
            if (
              typeof item ===
              "string"
            ) {
              return item;
            }

            if (
              item &&
              typeof item.msg ===
                "string"
            ) {
              return item.msg;
            }

            return null;
          },
        )
        .filter(Boolean)
        .join(", ");
    }
  }

  return "An error occurred while processing the email parsing request.";
}


// ============================================================================
// SERVICE OBJECT
// ============================================================================

export const parsingService =
  Object.freeze({
    // Health / summary
    getParsingHealth,
    getParsingSummary,

    // Workspace
    getParsingEmails,

    // Selection
    getMatchingEmailIds,
    getPendingEmailIds,
    selectAllMatchingEmails,

    // Parsed email details
    getParsedEmail,

    // Parsing actions
    parseEmail,
    parseEmails,
    parseSelectedEmails,
    parseMatchingEmails,
    parseAllPending,

    // Response helpers
    normalizeBatchParsingResponse,

    // Error helpers
    getParsingServiceErrorMessage,
  });


export default parsingService;
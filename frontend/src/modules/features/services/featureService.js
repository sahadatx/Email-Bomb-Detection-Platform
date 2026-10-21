/**
 * Module 04 — Feature Engineering
 *
 * Frontend API service for the F1-F12 Feature Engineering
 * module.
 *
 * Responsibilities:
 * - Communicate with the Feature Engineering API
 * - Build API requests
 * - Normalize API responses
 * - Normalize API errors
 * - Provide workspace operations
 * - Provide workspace filtering
 * - Provide global selection operations
 * - Provide feature detail operations
 * - Provide extraction operations
 * - Provide right-side Feature Details drawer data
 *
 * No UI rendering.
 * No ML/classification.
 * No prediction.
 * No confidence scoring.
 * No risk scoring.
 * No threat scoring.
 */

import apiClient from "../../../core/api/client";

import {
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
  MAX_PAGE_SIZE,

  normalizeFeatureResponse,
  normalizeFeatureListResponse,
  normalizeFeatureSelectionResponse,
  normalizeFeatureSummary,
  normalizeFeatureDefinitions,
  normalizeFeatureHealth,
  normalizeExtractionResponse,

  buildExtractionRequest,
  buildBatchExtractionRequest,
} from "../types";


// ============================================================
// API CONFIGURATION
// ============================================================

const API_PREFIX = "/features";


// ============================================================
// API ERROR
// ============================================================

export class FeatureApiError extends Error {
  constructor(
    message,
    {
      status = null,
      code = null,
      details = null,
      data = null,
    } = {},
  ) {
    super(message);

    this.name = "FeatureApiError";

    this.status = status;

    this.code = code;

    this.details = details;

    this.data = data;
  }
}


// ============================================================
// INPUT NORMALIZATION
// ============================================================

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


function normalizeForce(value) {
  return Boolean(value);
}


function normalizeFilterText(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return null;
  }

  const normalized =
    String(value).trim();

  return normalized || null;
}


function normalizeFilterValue(value) {
  return (
    normalizeFilterText(value)
      ?.toLowerCase() ??
    null
  );
}


function normalizeDateFilter(value) {
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
      ).padStart(
        2,
        "0",
      );

    const day =
      String(
        value.getDate(),
      ).padStart(
        2,
        "0",
      );

    return `${year}-${month}-${day}`;
  }

  const normalized =
    String(value).trim();

  if (!normalized) {
    return null;
  }

  /*
   * Backend expects date values in YYYY-MM-DD format.
   */

  return normalized.slice(
    0,
    10,
  );
}


// ============================================================
// WORKSPACE FILTER NORMALIZATION
// ============================================================

function normalizeWorkspaceFilters(
  filters = {},
) {
  return {
    search:
      normalizeFilterText(
        filters.search,
      ),

    source:
      normalizeFilterValue(
        filters.source,
      ),

    level:
      normalizeFilterValue(
        filters.level,
      ),

    status:
      normalizeFilterValue(
        filters.status,
      ),

    from_date:
      normalizeDateFilter(
        filters.from_date ??
        filters.fromDate,
      ),

    to_date:
      normalizeDateFilter(
        filters.to_date ??
        filters.toDate,
      ),
  };
}


// ============================================================
// ERROR NORMALIZATION
// ============================================================

function extractErrorMessage(error) {
  if (
    error instanceof
    FeatureApiError
  ) {
    return error.message;
  }

  if (
    error?.response?.data
      ?.error?.message
  ) {
    return (
      error.response.data
        .error.message
    );
  }

  if (
    error?.response?.data
      ?.message
  ) {
    return (
      error.response.data.message
    );
  }

  if (
    error?.data?.error?.message
  ) {
    return (
      error.data.error.message
    );
  }

  if (
    error?.data?.message
  ) {
    return error.data.message;
  }

  if (error?.message) {
    return error.message;
  }

  return (
    "Feature API request failed."
  );
}


function toFeatureApiError(error) {
  if (
    error instanceof
    FeatureApiError
  ) {
    return error;
  }

  const status =
    error?.response?.status ??
    error?.status ??
    null;

  const data =
    error?.response?.data ??
    error?.data ??
    null;

  const code =
    data?.error?.code ??
    data?.code ??
    null;

  const details =
    data?.error?.details ??
    data?.details ??
    null;

  return new FeatureApiError(
    extractErrorMessage(error),
    {
      status,
      code,
      details,
      data,
    },
  );
}


// ============================================================
// REQUEST WRAPPER
// ============================================================

async function request(
  path,
  {
    method = "GET",
    body,
    signal,
  } = {},
) {
  try {
    let response;

    switch (method) {
      case "GET": {
        response =
          await apiClient.get(
            `${API_PREFIX}${path}`,
            {
              signal,
            },
          );

        break;
      }

      case "POST": {
        response =
          await apiClient.post(
            `${API_PREFIX}${path}`,
            body,
            {
              signal,
            },
          );

        break;
      }

      case "DELETE": {
        response =
          await apiClient.delete(
            `${API_PREFIX}${path}`,
            {
              signal,
            },
          );

        break;
      }

      default:
        throw new FeatureApiError(
          `Unsupported HTTP method: ${method}`,
          {
            code:
              "FEATURE_HTTP_METHOD_UNSUPPORTED",
          },
        );
    }

    return response?.data;

  } catch (error) {
    /*
     * Preserve cancellation errors so callers can distinguish
     * them from actual API failures.
     */

    if (
      error?.name ===
      "AbortError"
    ) {
      throw error;
    }

    if (
      error?.code ===
      "ERR_CANCELED"
    ) {
      throw error;
    }

    throw toFeatureApiError(
      error,
    );
  }
}


// ============================================================
// BUILD WORKSPACE QUERY PARAMETERS
// ============================================================

function buildWorkspaceQueryParams({
  page,
  pageSize,
  filters,
}) {
  const params =
    new URLSearchParams();

  params.set(
    "page",
    String(page),
  );

  params.set(
    "page_size",
    String(pageSize),
  );

  const normalizedFilters =
    normalizeWorkspaceFilters(
      filters,
    );

  if (
    normalizedFilters.search
  ) {
    params.set(
      "search",
      normalizedFilters.search,
    );
  }

  if (
    normalizedFilters.source
  ) {
    params.set(
      "source",
      normalizedFilters.source,
    );
  }

  if (
    normalizedFilters.level
  ) {
    params.set(
      "level",
      normalizedFilters.level,
    );
  }

  if (
    normalizedFilters.status
  ) {
    params.set(
      "status",
      normalizedFilters.status,
    );
  }

  if (
    normalizedFilters.from_date
  ) {
    params.set(
      "from_date",
      normalizedFilters.from_date,
    );
  }

  if (
    normalizedFilters.to_date
  ) {
    params.set(
      "to_date",
      normalizedFilters.to_date,
    );
  }

  return params;
}


// ============================================================
// BUILD SELECTION REQUEST BODY
// ============================================================
//
// The backend selection endpoint receives the same canonical
// workspace filters.
//
// POST /features/selection
//
// Important:
// Selection is resolved against the COMPLETE filtered
// result set, not the current UI page.
//

function buildSelectionRequestBody(
  filters = {},
) {
  const normalizedFilters =
    normalizeWorkspaceFilters(
      filters,
    );

  return {
    search:
      normalizedFilters.search,

    source:
      normalizedFilters.source,

    level:
      normalizedFilters.level,

    status:
      normalizedFilters.status,

    from_date:
      normalizedFilters.from_date,

    to_date:
      normalizedFilters.to_date,
  };
}


// ============================================================
// GET FEATURE WORKSPACE
// ============================================================

export async function getFeatures({
  page = DEFAULT_PAGE,
  pageSize = DEFAULT_PAGE_SIZE,

  /*
   * Canonical workspace filter object.
   */
  filters = {},

  /*
   * Backward-compatible direct filters.
   */
  search,
  source,
  level,
  status,
  fromDate,
  toDate,
  from_date,
  to_date,

  signal,
} = {}) {
  const normalizedPage =
    normalizePage(page);

  const normalizedPageSize =
    normalizePageSize(
      pageSize,
    );

  const mergedFilters = {
    ...filters,

    ...(search !== undefined
      ? { search }
      : {}),

    ...(source !== undefined
      ? { source }
      : {}),

    ...(level !== undefined
      ? { level }
      : {}),

    ...(status !== undefined
      ? { status }
      : {}),

    ...(fromDate !== undefined
      ? { fromDate }
      : {}),

    ...(toDate !== undefined
      ? { toDate }
      : {}),

    ...(from_date !== undefined
      ? { from_date }
      : {}),

    ...(to_date !== undefined
      ? { to_date }
      : {}),
  };

  const params =
    buildWorkspaceQueryParams({
      page:
        normalizedPage,

      pageSize:
        normalizedPageSize,

      filters:
        mergedFilters,
    });

  const data =
    await request(
      `/?${params.toString()}`,
      {
        method: "GET",
        signal,
      },
    );

  return normalizeFeatureListResponse(
    data,
  );
}


// ============================================================
// RESOLVE GLOBAL FEATURE SELECTION
// ============================================================
//
// This endpoint is specifically used by:
//
//     Select All Matching
//
// It does NOT depend on the current page.
//
// Example:
//
//     UI page size = 30
//     Matching emails = 500
//
// The backend returns all selectable IDs among those 500.
//

export async function getFeatureSelection(
  filters = {},
  {
    signal,
  } = {},
) {
  const body =
    buildSelectionRequestBody(
      filters,
    );

  const data =
    await request(
      "/selection",
      {
        method: "POST",
        body,
        signal,
      },
    );

  return normalizeFeatureSelectionResponse(
    data,
  );
}


// ============================================================
// GET SINGLE FEATURE
// ============================================================
//
// Used by the right-side Feature Details drawer.
//

export async function getFeature(
  emailId,
  {
    signal,
  } = {},
) {
  const normalizedEmailId =
    normalizeEmailId(
      emailId,
    );

  if (
    !normalizedEmailId
  ) {
    throw new FeatureApiError(
      "emailId is required to retrieve feature details.",
      {
        code:
          "FEATURE_EMAIL_ID_REQUIRED",
      },
    );
  }

  const encodedEmailId =
    encodeURIComponent(
      normalizedEmailId,
    );

  const data =
    await request(
      `/${encodedEmailId}`,
      {
        method: "GET",
        signal,
      },
    );

  return normalizeFeatureResponse(
    data,
  );
}


// ============================================================
// GET FEATURE SUMMARY
// ============================================================

export async function getFeatureSummary({
  signal,
} = {}) {
  const data =
    await request(
      "/summary",
      {
        method: "GET",
        signal,
      },
    );

  return normalizeFeatureSummary(
    data,
  );
}


// ============================================================
// GET FEATURE DEFINITIONS
// ============================================================

export async function getFeatureDefinitions({
  signal,
} = {}) {
  const data =
    await request(
      "/definitions",
      {
        method: "GET",
        signal,
      },
    );

  return normalizeFeatureDefinitions(
    data,
  );
}


// ============================================================
// GET FEATURE HEALTH
// ============================================================

export async function getFeatureHealth({
  signal,
} = {}) {
  const data =
    await request(
      "/health",
      {
        method: "GET",
        signal,
      },
    );

  return normalizeFeatureHealth(
    data,
  );
}


// ============================================================
// EXTRACT FEATURES — SINGLE EMAIL
// ============================================================

export async function extractFeatures(
  emailId,
  {
    force = false,
    signal,
  } = {},
) {
  const normalizedEmailId =
    normalizeEmailId(
      emailId,
    );

  if (
    !normalizedEmailId
  ) {
    throw new FeatureApiError(
      "emailId is required for feature extraction.",
      {
        code:
          "FEATURE_EMAIL_ID_REQUIRED",
      },
    );
  }

  const body =
    buildExtractionRequest(
      normalizeForce(force),
    );

  const encodedEmailId =
    encodeURIComponent(
      normalizedEmailId,
    );

  const data =
    await request(
      `/${encodedEmailId}/extract`,
      {
        method: "POST",
        body,
        signal,
      },
    );

  return normalizeFeatureResponse(
    data,
  );
}


// ============================================================
// RE-EXTRACT FEATURES — SINGLE EMAIL
// ============================================================

export async function reextractFeatures(
  emailId,
  {
    signal,
  } = {},
) {
  const normalizedEmailId =
    normalizeEmailId(
      emailId,
    );

  if (
    !normalizedEmailId
  ) {
    throw new FeatureApiError(
      "emailId is required for feature re-extraction.",
      {
        code:
          "FEATURE_EMAIL_ID_REQUIRED",
      },
    );
  }

  const encodedEmailId =
    encodeURIComponent(
      normalizedEmailId,
    );

  const data =
    await request(
      `/${encodedEmailId}/reextract`,
      {
        method: "POST",
        signal,
      },
    );

  return normalizeFeatureResponse(
    data,
  );
}


// ============================================================
// BATCH FEATURE EXTRACTION
// ============================================================
//
// The UI can chunk large selections into batches of <=100.
// This service validates and deduplicates one batch.
//

export async function extractFeaturesBatch(
  emailIds,
  {
    force = false,
    signal,
  } = {},
) {
  const ids =
    normalizeEmailIds(
      emailIds,
    );

  if (
    ids.length === 0
  ) {
    throw new FeatureApiError(
      "At least one emailId is required for batch feature extraction.",
      {
        code:
          "FEATURE_EMAIL_IDS_REQUIRED",
      },
    );
  }

  if (ids.length > MAX_PAGE_SIZE) {
    throw new FeatureApiError(
      `Batch feature extraction supports a maximum of ${MAX_PAGE_SIZE} emails per request.`,
      {
        code:
          "FEATURE_BATCH_SIZE_EXCEEDED",
      },
    );
  }

  const body =
    buildBatchExtractionRequest(
      ids,
      normalizeForce(force),
    );

  const data =
    await request(
      "/batch/extract",
      {
        method: "POST",
        body,
        signal,
      },
    );

  return normalizeExtractionResponse(
    data,
  );
}


// ============================================================
// DELETE FEATURE
// ============================================================

export async function deleteFeature(
  emailId,
  {
    signal,
  } = {},
) {
  const normalizedEmailId =
    normalizeEmailId(
      emailId,
    );

  if (
    !normalizedEmailId
  ) {
    throw new FeatureApiError(
      "emailId is required to delete feature data.",
      {
        code:
          "FEATURE_EMAIL_ID_REQUIRED",
      },
    );
  }

  const encodedEmailId =
    encodeURIComponent(
      normalizedEmailId,
    );

  const data =
    await request(
      `/${encodedEmailId}`,
      {
        method: "DELETE",
        signal,
      },
    );

  return data ?? null;
}


// ============================================================
// REFRESH WORKSPACE
// ============================================================
//
// Workspace data uses filters.
// Summary remains global and unfiltered.
//

export async function refreshFeatureWorkspace({
  page = DEFAULT_PAGE,
  pageSize = DEFAULT_PAGE_SIZE,
  filters = {},
  signal,
} = {}) {
  const [
    features,
    summary,
  ] = await Promise.all([
    getFeatures({
      page,
      pageSize,
      filters,
      signal,
    }),

    getFeatureSummary({
      signal,
    }),
  ]);

  return {
    features,
    summary,
  };
}


// ============================================================
// LOAD FEATURE MODULE METADATA
// ============================================================

export async function loadFeatureModuleMetadata({
  signal,
} = {}) {
  const [
    health,
    definitions,
  ] = await Promise.all([
    getFeatureHealth({
      signal,
    }),

    getFeatureDefinitions({
      signal,
    }),
  ]);

  return {
    health,
    definitions,
  };
}


// ============================================================
// RIGHT-SIDE FEATURE DETAILS DRAWER
// ============================================================

export async function getFeatureDetailsForDrawer(
  emailId,
  {
    signal,
  } = {},
) {
  return getFeature(
    emailId,
    {
      signal,
    },
  );
}


// ============================================================
// EXTRACT + GET DETAIL
// ============================================================

export async function extractAndGetFeature(
  emailId,
  {
    force = false,
    signal,
  } = {},
) {
  await extractFeatures(
    emailId,
    {
      force,
      signal,
    },
  );

  return getFeature(
    emailId,
    {
      signal,
    },
  );
}


// ============================================================
// RE-EXTRACT + GET DETAIL
// ============================================================

export async function reextractAndGetFeature(
  emailId,
  {
    signal,
  } = {},
) {
  await reextractFeatures(
    emailId,
    {
      signal,
    },
  );

  return getFeature(
    emailId,
    {
      signal,
    },
  );
}


// ============================================================
// EMPTY WORKSPACE FILTERS
// ============================================================
//
// This service helper uses API field names.
//

export function createEmptyWorkspaceFilters() {
  return {
    search: null,

    source: null,

    level: null,

    status: null,

    from_date: null,

    to_date: null,
  };
}


// ============================================================
// PUBLIC FILTER NORMALIZATION
// ============================================================

export function normalizeFeatureWorkspaceFilters(
  filters = {},
) {
  return normalizeWorkspaceFilters(
    filters,
  );
}


// ============================================================
// DEFAULT SERVICE
// ============================================================

const featureService = Object.freeze({
  // Workspace
  getFeatures,
  refreshFeatureWorkspace,

  // Global selection
  getFeatureSelection,

  // Filter helpers
  createEmptyWorkspaceFilters,
  normalizeFeatureWorkspaceFilters,

  // Summary
  getFeatureSummary,

  // Feature details
  getFeature,
  getFeatureDetailsForDrawer,

  // Definitions / health
  getFeatureDefinitions,
  getFeatureHealth,
  loadFeatureModuleMetadata,

  // Extraction
  extractFeatures,
  reextractFeatures,
  extractFeaturesBatch,

  // Extraction + detail refresh
  extractAndGetFeature,
  reextractAndGetFeature,

  // Feature record management
  deleteFeature,
});


export default featureService;
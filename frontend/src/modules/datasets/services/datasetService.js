
import {
  DATASET_EXPORT_FORMAT,
  DATASET_EXPORT_SPLIT,
  WORKSPACE_PAGE_SIZE,
} from "../types";
import { getAuthState } from "../../../core/auth/authState";

/**
 * Module 05 — Dataset Management
 *
 * Centralized API service for:
 * - Dataset Workspace
 * - Dataset CRUD
 * - Dataset Email Management
 * - Dataset Versions
 * - Dataset Validation
 * - Dataset Export
 *
 * Backend:
 *   backend/app/modules/datasets/routes.py
 *
 * API prefix:
 *   /api/v1
 *
 * Environment:
 *   VITE_API_BASE_URL
 */

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "/api/v1"
).replace(/\/+$/, "");

const DATASETS_ENDPOINT = `${API_BASE_URL}/datasets`;

const DEFAULT_PAGE_SIZE = 30;
const MAX_PAGE_SIZE = 100;
const DEFAULT_PREVIEW_LIMIT = 20;

// ============================================================================
// URL HELPERS
// ============================================================================

function buildUrl(path, params = {}) {
  const url = new URL(path, window.location.origin);

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }

    if (typeof value === "object" && !Array.isArray(value)) {
      throw new TypeError(
        `Query parameter "${key}" must not be an object.`
      );
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== undefined && item !== null && item !== "") {
          url.searchParams.append(key, String(item));
        }
      }
      continue;
    }

    url.searchParams.set(key, String(value));
  }

  return url.toString();
}

function normalizePageParams(params = {}) {
  const page = Number(params.page ?? 1);
  const requestedPageSize = Number(
    params.page_size ??
      WORKSPACE_PAGE_SIZE ??
      DEFAULT_PAGE_SIZE
  );

  if (!Number.isInteger(page) || page < 1) {
    throw new Error("Page must be a positive integer.");
  }

  if (
    !Number.isInteger(requestedPageSize) ||
    requestedPageSize < 1
  ) {
    throw new Error("Page size must be a positive integer.");
  }

  return {
    page,
    page_size: Math.min(requestedPageSize, MAX_PAGE_SIZE),
  };
}

function normalizeWorkspaceParams(params = {}) {
  const filters = params.filters ?? {};

  return {
    ...normalizePageParams(params),
    search: params.search ?? filters.search,
    ground_truth:
      params.ground_truth ?? filters.ground_truth,
    source: params.source ?? filters.source,
    from_date: params.from_date ?? filters.from_date,
    to_date: params.to_date ?? filters.to_date,
  };
}

function normalizeEmailListParams(params = {}) {
  const normalized = normalizePageParams(params);

  return {
    ...normalized,
    search: params.search?.trim() || undefined,
  };
}

// ============================================================================
// RESPONSE AND ERROR HANDLING
// ============================================================================

async function parseResponse(response) {
  if (response.status === 204) {
    return null;
  }

  const contentType =
    response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  if (
    contentType.includes("text/") ||
    contentType.includes("application/xml")
  ) {
    return response.text();
  }

  return response.blob();
}

function formatValidationDetail(detail) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const location = Array.isArray(item?.loc)
          ? item.loc.join(".")
          : "";

        const message =
          item?.msg ??
          item?.message ??
          String(item);

        return location ? `${location}: ${message}` : message;
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return "";
}

function getErrorMessage(payload, fallback) {
  const detail = formatValidationDetail(payload?.detail);

  if (detail) {
    return detail;
  }

  if (typeof payload?.message === "string") {
    return payload.message;
  }

  if (typeof payload?.error === "string") {
    return payload.error;
  }

  if (typeof payload?.error?.message === "string") {
    return payload.error.message;
  }

  return fallback;
}

function getRequestHeaders(headers = {}, accept = "application/json") {
  const requestHeaders = {
    Accept: accept,
    ...headers,
  };

  // Match the bearer-token authentication used by the other modules.
  const accessToken = getAuthState()?.accessToken;
  if (accessToken) {
    requestHeaders.Authorization = `Bearer ${accessToken}`;
  }

  return requestHeaders;
}

function createApiError(message, statusCode, payload = null) {
  const error = new Error(message || "API request failed.");

  error.name = "DatasetApiError";
  error.status = statusCode;
  error.code =
    payload?.code ??
    payload?.error?.code ??
    null;

  error.details =
    payload?.detail ??
    payload?.details ??
    payload?.error?.details ??
    payload ??
    null;

  error.response = {
    status: statusCode,
    data: payload,
  };

  return error;
}

async function request(path, options = {}) {
  const {
    params,
    body,
    headers = {},
    ...fetchOptions
  } = options;

  const url = buildUrl(path, params);

  const requestOptions = {
    credentials: "include",
    ...fetchOptions,
    headers: getRequestHeaders(headers),
  };

  if (body !== undefined) {
    if (
      typeof FormData !== "undefined" &&
      body instanceof FormData
    ) {
      requestOptions.body = body;
    } else {
      requestOptions.body = JSON.stringify(body);
      requestOptions.headers["Content-Type"] = "application/json";
    }
  }

  let response;

  try {
    response = await fetch(url, requestOptions);
  } catch (cause) {
    const error = createApiError(
      "Unable to connect to the Dataset Management API.",
      undefined
    );

    error.code = "NETWORK_ERROR";
    error.cause = cause;
    throw error;
  }

  if (!response.ok) {
    const payload = await parseResponse(response).catch(
      () => null
    );

    throw createApiError(
      getErrorMessage(
        payload,
        `Request failed with status ${response.status}.`
      ),
      response.status,
      payload
    );
  }

  return parseResponse(response);
}

// ============================================================================
// COMMON VALIDATION
// ============================================================================

function requireId(value, fieldName) {
  if (
    value === undefined ||
    value === null ||
    String(value).trim() === ""
  ) {
    throw new Error(`${fieldName} is required.`);
  }

  return encodeURIComponent(String(value).trim());
}

function normalizeEmailIds(emailIds) {
  if (!Array.isArray(emailIds) || emailIds.length === 0) {
    throw new Error("Select at least one email.");
  }

  const normalized = emailIds.map((id) => {
    if (id === undefined || id === null || !String(id).trim()) {
      throw new Error("Every selected email must have an ID.");
    }

    return String(id).trim();
  });

  if (new Set(normalized).size !== normalized.length) {
    throw new Error("Duplicate email IDs are not allowed.");
  }

  return normalized;
}

function normalizeExportFormat(
  format = DATASET_EXPORT_FORMAT.CSV
) {
  if (
    !Object.values(DATASET_EXPORT_FORMAT).includes(format)
  ) {
    throw new Error(`Unsupported export format: ${format}`);
  }

  return format;
}

function normalizeExportSplit(
  split = DATASET_EXPORT_SPLIT.ALL
) {
  if (
    !Object.values(DATASET_EXPORT_SPLIT).includes(split)
  ) {
    throw new Error(`Unsupported export split: ${split}`);
  }

  return split;
}

// ============================================================================
// WORKSPACE
// ============================================================================

/**
 * GET /datasets
 *
 * Returns eligible, feature-extracted emails.
 */
export async function getWorkspace(params = {}) {
  return request(DATASETS_ENDPOINT, {
    method: "GET",
    params: normalizeWorkspaceParams(params),
  });
}

/**
 * GET /datasets/samples/{email_id}
 *
 * Returns a single workspace email.
 */
export async function getWorkspaceEmail(emailId) {
  const id = requireId(emailId, "emailId");

  return request(`${DATASETS_ENDPOINT}/samples/${id}`);
}

/**
 * GET /datasets/selection
 *
 * Resolve all matching email IDs.
 */
export async function selectAllMatching(filters = {}) {
  const params = normalizeWorkspaceParams({
    ...filters,
    page: undefined,
    page_size: undefined,
  });

  delete params.page;
  delete params.page_size;

  return request(`${DATASETS_ENDPOINT}/selection`, {
    method: "GET",
    params,
  });
}

/**
 * POST /datasets/selection
 *
 * Resolve explicit selection.
 */
export async function resolveSelection(payload = {}) {
  return request(`${DATASETS_ENDPOINT}/selection`, {
    method: "POST",
    body: payload,
  });
}

// ============================================================================
// DATASET SUMMARY
// ============================================================================

/**
 * GET /datasets/summary
 */
export async function getDatasetSummary() {
  return request(`${DATASETS_ENDPOINT}/summary`);
}

// ============================================================================
// DATASET CRUD
// ============================================================================

/**
 * GET /datasets/list
 */
export async function getDatasets(params = {}) {
  return request(`${DATASETS_ENDPOINT}/list`, {
    method: "GET",
    params: normalizePageParams(params),
  });
}

/**
 * Compatibility alias.
 */
export const listDatasets = getDatasets;

/**
 * GET /datasets/{dataset_id}
 */
export async function getDataset(datasetId) {
  const id = requireId(datasetId, "datasetId");

  return request(`${DATASETS_ENDPOINT}/${id}`);
}

/**
 * POST /datasets
 *
 * Create a dataset using selected eligible email IDs.
 */
export async function createDataset(payload = {}) {
  const name = String(payload.name ?? "").trim();

  if (!name) {
    throw new Error("Dataset name is required.");
  }

  const emailIds = normalizeEmailIds(payload.email_ids);

  return request(DATASETS_ENDPOINT, {
    method: "POST",
    body: {
      ...payload,
      name,
      description: payload.description
        ? String(payload.description).trim()
        : null,
      email_ids: emailIds,
    },
  });
}

/**
 * PATCH /datasets/{dataset_id}
 *
 * Update dataset metadata.
 */
export async function updateDataset(datasetId, payload = {}) {
  const id = requireId(datasetId, "datasetId");
  const body = {};

  if (Object.prototype.hasOwnProperty.call(payload, "name")) {
    const name = String(payload.name ?? "").trim();

    if (!name) {
      throw new Error("Dataset name is required.");
    }

    body.name = name;
  }

  if (
    Object.prototype.hasOwnProperty.call(
      payload,
      "description"
    )
  ) {
    body.description = payload.description
      ? String(payload.description).trim()
      : null;
  }

  if (Object.keys(body).length === 0) {
    throw new Error("No dataset changes were provided.");
  }

  return request(`${DATASETS_ENDPOINT}/${id}`, {
    method: "PATCH",
    body,
  });
}

/**
 * Compatibility alias.
 */
export const editDataset = updateDataset;

/**
 * POST /datasets/{dataset_id}/archive
 */
export async function archiveDataset(datasetId) {
  const id = requireId(datasetId, "datasetId");

  return request(`${DATASETS_ENDPOINT}/${id}/archive`, {
    method: "POST",
  });
}

// ============================================================================
// DATASET EMAIL MANAGEMENT
// ============================================================================

/**
 * GET /datasets/{dataset_id}/emails
 *
 * List emails belonging to a dataset.
 *
 * Query:
 *   page
 *   page_size
 *   search
 */
export async function getDatasetEmails(datasetId, params = {}) {
  const id = requireId(datasetId, "datasetId");

  return request(`${DATASETS_ENDPOINT}/${id}/emails`, {
    method: "GET",
    params: normalizeEmailListParams(params),
  });
}

/**
 * Compatibility alias.
 */
export const listDatasetEmails = getDatasetEmails;

/**
 * POST /datasets/{dataset_id}/emails
 *
 * Add eligible extracted emails to a dataset.
 *
 * Body:
 * {
 *   email_ids: ["uuid", ...]
 * }
 */
export async function addDatasetEmails(
  datasetId,
  emailIds
) {
  const id = requireId(datasetId, "datasetId");
  const normalizedIds = normalizeEmailIds(emailIds);

  return request(`${DATASETS_ENDPOINT}/${id}/emails`, {
    method: "POST",
    body: {
      email_ids: normalizedIds,
    },
  });
}

/**
 * DELETE /datasets/{dataset_id}/emails
 *
 * Remove DatasetSample membership only.
 * Canonical Email records and existing version snapshots
 * must remain untouched by the backend.
 */
export async function removeDatasetEmails(
  datasetId,
  emailIds
) {
  const id = requireId(datasetId, "datasetId");
  const normalizedIds = normalizeEmailIds(emailIds);

  return request(`${DATASETS_ENDPOINT}/${id}/emails`, {
    method: "DELETE",
    body: {
      email_ids: normalizedIds,
    },
  });
}

// ============================================================================
// DATASET VERSIONS
// ============================================================================

/**
 * GET /datasets/{dataset_id}/versions
 */
export async function getVersionsForDataset(
  datasetId,
  params = {}
) {
  const id = requireId(datasetId, "datasetId");

  return request(`${DATASETS_ENDPOINT}/${id}/versions`, {
    method: "GET",
    params: normalizePageParams(params),
  });
}

/**
 * List versions using the page's params object.
 *
 * Supports:
 *   getDatasetVersions({ dataset_id, page, page_size })
 */
export async function getDatasetVersions(params = {}) {
  if (!params.dataset_id) {
    throw new Error(
      "Select a dataset to list its versions."
    );
  }

  return getVersionsForDataset(params.dataset_id, params);
}

/**
 * Compatibility alias.
 */
export const listVersions = getDatasetVersions;

/**
 * GET /datasets/versions/{version_id}
 */
export async function getDatasetVersion(versionId) {
  const id = requireId(versionId, "versionId");

  return request(`${DATASETS_ENDPOINT}/versions/${id}`);
}

/**
 * Compatibility alias.
 */
export const getVersion = getDatasetVersion;

/**
 * POST /datasets/versions
 *
 * Create an immutable dataset version.
 *
 * Expected payload:
 * {
 *   dataset_id: string,
 *   name: string,
 *   split: {
 *     training_percentage: number,
 *     validation_percentage: number,
 *     testing_percentage: number,
 *     random_seed: number,
 *     stratified: boolean
 *   }
 * }
 */
export async function createDatasetVersion(payload = {}) {
  const datasetId = String(
    payload.dataset_id ?? ""
  ).trim();

  const name = String(payload.name ?? "").trim();

  if (!datasetId) {
    throw new Error("dataset_id is required.");
  }

  if (!name) {
    throw new Error("Version name is required.");
  }

  const sourceSplit = payload.split ?? {};

  const training = Number(
    sourceSplit.training_percentage ??
      sourceSplit.train_percent
  );

  const validation = Number(
    sourceSplit.validation_percentage ??
      sourceSplit.validation_percent
  );

  const testing = Number(
    sourceSplit.testing_percentage ??
      sourceSplit.test_percent
  );

  const randomSeed = Number(
    sourceSplit.random_seed ??
      sourceSplit.randomSeed ??
      42
  );

  const stratified = sourceSplit.stratified ?? true;

  const percentages = [training, validation, testing];

  if (
    percentages.some(
      (value) =>
        !Number.isInteger(value) ||
        value < 0 ||
        value > 100
    )
  ) {
    throw new Error(
      "Split percentages must be whole numbers between 0 and 100."
    );
  }

  if (
    percentages.reduce((sum, value) => sum + value, 0) !==
    100
  ) {
    throw new Error(
      "Split percentages must total exactly 100%."
    );
  }

  if (!Number.isInteger(randomSeed) || randomSeed < 0) {
    throw new Error(
      "Random seed must be a non-negative integer."
    );
  }

  if (typeof stratified !== "boolean") {
    throw new Error("Stratified must be a boolean value.");
  }

  return request(`${DATASETS_ENDPOINT}/versions`, {
    method: "POST",
    body: {
      dataset_id: datasetId,
      name,
      split: {
        training_percentage: training,
        validation_percentage: validation,
        testing_percentage: testing,
        random_seed: randomSeed,
        stratified,
      },
    },
  });
}

/**
 * Compatibility alias.
 */
export const createVersion = createDatasetVersion;

/**
 * GET /datasets/versions/{version_id}/samples
 *
 * Returns email IDs, optionally filtered by split.
 */
export async function getVersionSampleIds(
  versionId,
  params = {}
) {
  const id = requireId(versionId, "versionId");

  return request(
    `${DATASETS_ENDPOINT}/versions/${id}/samples`,
    {
      method: "GET",
      params: {
        split: params.split,
      },
    }
  );
}

/**
 * Compatibility helper.
 *
 * The backend endpoint returns sample IDs,
 * not full membership objects.
 */
export async function getVersionMemberships(
  versionId,
  params = {}
) {
  return getVersionSampleIds(versionId, params);
}

// ============================================================================
// DATASET VALIDATION
// ============================================================================

/**
 * POST /datasets/versions/{version_id}/validate
 */
export async function validateDatasetVersion(versionId) {
  const id = requireId(versionId, "versionId");

  return request(
    `${DATASETS_ENDPOINT}/versions/${id}/validate`,
    {
      method: "POST",
    }
  );
}

/**
 * Compatibility wrapper.
 */
export async function validateDataset(payload = {}) {
  if (!payload.version_id) {
    throw new Error(
      "version_id is required. The backend validates dataset versions."
    );
  }

  return validateDatasetVersion(payload.version_id);
}

/**
 * The backend does not expose a GET validation-result route.
 */
export async function getDatasetValidation(
  datasetId,
  params = {}
) {
  if (!params.version_id) {
    throw new Error(
      "version_id is required. The backend does not expose a dataset-level validation GET route."
    );
  }

  return validateDatasetVersion(params.version_id);
}

// ============================================================================
// EXPORT PREVIEW
// ============================================================================

/**
 * GET /datasets/versions/{version_id}/export/preview
 */
export async function previewDatasetExport(payload = {}) {
  const versionId = requireId(
    payload.version_id,
    "version_id"
  );

  const split = normalizeExportSplit(payload.split);
  const limit = Number(
    payload.limit ?? DEFAULT_PREVIEW_LIMIT
  );

  if (
    !Number.isInteger(limit) ||
    limit < 1 ||
    limit > 100
  ) {
    throw new Error(
      "Preview limit must be between 1 and 100."
    );
  }

  return request(
    `${DATASETS_ENDPOINT}/versions/${versionId}/export/preview`,
    {
      method: "GET",
      params: {
        split,
        limit,
      },
    }
  );
}

// ============================================================================
// EXPORT
// ============================================================================

/**
 * GET /datasets/versions/{version_id}/export
 *
 * Returns a Blob for download.
 */
export async function exportDataset(payload = {}) {
  const versionId = requireId(
    payload.version_id,
    "version_id"
  );

  const format = normalizeExportFormat(payload.format);
  const split = normalizeExportSplit(payload.split);

  const url = buildUrl(
    `${DATASETS_ENDPOINT}/versions/${versionId}/export`,
    {
      format,
      split,
    }
  );

  let response;

  try {
    response = await fetch(url, {
      method: "GET",
      credentials: "include",
      headers: getRequestHeaders(
        {},
        format === DATASET_EXPORT_FORMAT.CSV
          ? "text/csv"
          : "application/json"
      ),
    });
  } catch (cause) {
    const error = createApiError(
      "Unable to connect to the Dataset export API.",
      undefined
    );

    error.code = "NETWORK_ERROR";
    error.cause = cause;
    throw error;
  }

  if (!response.ok) {
    const payload = await parseResponse(response).catch(
      () => null
    );

    throw createApiError(
      getErrorMessage(
        payload,
        `Export failed with status ${response.status}.`
      ),
      response.status,
      payload
    );
  }

  return response.blob();
}

/**
 * Trigger a browser download from an export Blob.
 */
export function downloadExport(
  blob,
  filename = "dataset-export"
) {
  if (
    typeof Blob === "undefined" ||
    !(blob instanceof Blob)
  ) {
    throw new TypeError(
      "A Blob is required to download an export."
    );
  }

  const safeFilename = String(filename)
    .replace(/[<>:"/\\|?*\u0000-\u001F]/g, "_")
    .trim();

  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = objectUrl;
  anchor.download =
    safeFilename || "dataset-export";
  anchor.style.display = "none";

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(objectUrl);
}

// ============================================================================
// DEFAULT SERVICE
// ============================================================================

const datasetService = Object.freeze({
  // Workspace
  getWorkspace,
  getWorkspaceEmail,
  selectAllMatching,
  resolveSelection,
  getDatasetSummary,

  // Datasets
  getDatasets,
  listDatasets,
  getDataset,
  createDataset,
  updateDataset,
  editDataset,
  archiveDataset,

  // Dataset Emails
  getDatasetEmails,
  listDatasetEmails,
  addDatasetEmails,
  removeDatasetEmails,

  // Versions
  getVersionsForDataset,
  getDatasetVersions,
  listVersions,
  getDatasetVersion,
  getVersion,
  createDatasetVersion,
  createVersion,
  getVersionSampleIds,
  getVersionMemberships,

  // Validation
  validateDataset,
  validateDatasetVersion,
  getDatasetValidation,

  // Export
  previewDatasetExport,
  exportDataset,
  downloadExport,
});

export default datasetService;

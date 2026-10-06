import { getAuthState } from "../auth/authState";
import { getApiErrorInfo } from "./errors";

// ============================================================
// API BASE URL
// ============================================================
//
// Development:
// Browser → Vite :5173 → /api proxy → FastAPI :8000
//
// If VITE_API_BASE_URL is explicitly provided, it can still
// override the default.
//
// ============================================================

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "/api/v1";

// ============================================================
// API ERROR
// ============================================================

export class ApiError extends Error {
  constructor(
    message,
    status,
    details = null,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.details = details;
    this.code = details?.error?.code || details?.code || "";
    this.title = getApiErrorInfo({ status, details, message }).title;
  }
}

// ============================================================
// RESPONSE PARSER
// ============================================================

async function parseResponse(response) {
  const contentType =
    response.headers.get(
      "content-type",
    ) || "";

  if (
    contentType.includes(
      "application/json",
    )
  ) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  return null;
}

// ============================================================
// REQUEST HEADERS
// ============================================================

function buildHeaders({
  body,
  headers = {},
  token,
}) {
  const requestHeaders = {
    Accept: "application/json",
    ...headers,
  };

  /*
   * Do not manually set Content-Type for FormData.
   * The browser must set multipart/form-data together
   * with the correct boundary.
   */
  if (
    body !== undefined &&
    !(body instanceof FormData)
  ) {
    requestHeaders[
      "Content-Type"
    ] = "application/json";
  }

  if (token) {
    requestHeaders.Authorization =
      `Bearer ${token}`;
  }

  return requestHeaders;
}

// ============================================================
// NORMALIZE REQUEST BODY
// ============================================================

function serializeBody(body) {
  if (body === undefined) {
    return undefined;
  }

  if (body instanceof FormData) {
    return body;
  }

  return JSON.stringify(body);
}

// ============================================================
// AUTH TOKEN
// ============================================================

function getStoredAccessToken() {
  try {
    return getAuthState()
      .accessToken;
  } catch {
    return null;
  }
}

// ============================================================
// CORE REQUEST
// ============================================================

export async function apiRequest(
  path,
  {
    method = "GET",
    body,
    token,
    headers = {},
    signal,
  } = {},
) {
  /*
   * Use an explicitly supplied token when available.
   * Otherwise automatically use the authenticated
   * session token.
   */
  const accessToken =
    token ??
    getStoredAccessToken();

  const requestHeaders =
    buildHeaders({
      body,
      headers,
      token: accessToken,
    });

  /*
   * API_BASE_URL is normally "/api/v1".
   *
   * Example:
   *   path = "/features"
   *   URL  = "/api/v1/features"
   */
  const url =
    `${API_BASE_URL}${path}`;

  let response;
  try {
    response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: serializeBody(body),
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError(
      "Could not connect to the server. Check your connection and try again.",
      0,
      { error: { code: "network_error", message: "Could not connect to the server." } },
    );
  }

  const data =
    await parseResponse(response);

  if (!response.ok) {
    const message = getApiErrorInfo({ status: response.status, details: data }).message;

    throw new ApiError(
      message,
      response.status,
      data,
    );
  }

  return data;
}

export async function apiDownload(path, filename) {
  const accessToken = getStoredAccessToken();
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json, application/pdf", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) },
    });
  } catch (error) {
    throw new ApiError("Could not connect to the server. Check your connection and try again.", 0, { error: { code: "network_error" } });
  }
  if (!response.ok) {
    const data = await parseResponse(response);
    const message = getApiErrorInfo({ status: response.status, details: data, message: "The download could not be completed." }).message;
    throw new ApiError(message, response.status, data);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

// ============================================================
// API CLIENT
// ============================================================
//
// Compatibility wrapper for module services.
// ============================================================

const apiClient = Object.freeze({
  request(
    path,
    options = {},
  ) {
    return apiRequest(
      path,
      options,
    );
  },

  get(
    path,
    options = {},
  ) {
    return apiRequest(
      path,
      {
        ...options,
        method: "GET",
      },
    ).then((data) => ({
      data,
    }));
  },

  post(
    path,
    body,
    options = {},
  ) {
    return apiRequest(
      path,
      {
        ...options,
        method: "POST",
        body,
      },
    ).then((data) => ({
      data,
    }));
  },

  put(
    path,
    body,
    options = {},
  ) {
    return apiRequest(
      path,
      {
        ...options,
        method: "PUT",
        body,
      },
    ).then((data) => ({
      data,
    }));
  },

  patch(
    path,
    body,
    options = {},
  ) {
    return apiRequest(
      path,
      {
        ...options,
        method: "PATCH",
        body,
      },
    ).then((data) => ({
      data,
    }));
  },

  delete(
    path,
    options = {},
  ) {
    return apiRequest(
      path,
      {
        ...options,
        method: "DELETE",
      },
    ).then((data) => ({
      data,
    }));
  },
});

// ============================================================
// HELPERS
// ============================================================

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export default apiClient;

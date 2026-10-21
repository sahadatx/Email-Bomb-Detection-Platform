import apiClient from "../../../core/api/client";

import {
  EMAIL_GROUND_TRUTH_LABELS,
  EMAIL_PAGINATION,
  EMAIL_SOURCES,
} from "../types";


// ============================================================
// CONSTANTS
// ============================================================

const EMAIL_BASE_PATH = "/emails";

const {
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
  MAX_PAGE_SIZE,
} = EMAIL_PAGINATION;


// ============================================================
// QUERY STRING
// ============================================================

function buildQueryString(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(
    ([key, value]) => {
      if (
        value === undefined ||
        value === null ||
        value === ""
      ) {
        return;
      }

      searchParams.append(
        key,
        String(value),
      );
    },
  );

  const query =
    searchParams.toString();

  return query
    ? `?${query}`
    : "";
}


// ============================================================
// PAGINATION NORMALIZATION
// ============================================================

function normalizePaginationResponse(
  response,
  {
    page = DEFAULT_PAGE,
    pageSize = DEFAULT_PAGE_SIZE,
  } = {},
) {
  const data = response ?? {};

  const totalValue =
    Number(data.total);

  const total =
    Number.isFinite(totalValue) &&
    totalValue >= 0
      ? totalValue
      : 0;


  const pageValue =
    Number(data.page);

  const normalizedPage =
    Number.isFinite(pageValue) &&
    pageValue >= 1
      ? pageValue
      : page;


  const pageSizeValue =
    Number(data.page_size);

  const normalizedPageSize =
    Number.isFinite(
      pageSizeValue,
    ) &&
    pageSizeValue >= 1
      ? Math.min(
          pageSizeValue,
          MAX_PAGE_SIZE,
        )
      : pageSize;


  const totalPagesValue =
    Number(data.total_pages);

  const calculatedTotalPages =
    total > 0
      ? Math.ceil(
          total /
            normalizedPageSize,
        )
      : 1;

  const totalPages =
    Number.isFinite(
      totalPagesValue,
    ) &&
    totalPagesValue >= 1
      ? totalPagesValue
      : Math.max(
          1,
          calculatedTotalPages,
        );


  const startIndexValue =
    Number(data.start_index);

  const calculatedStartIndex =
    total > 0
      ? (
          (normalizedPage - 1) *
            normalizedPageSize
        ) + 1
      : 0;

  const startIndex =
    Number.isFinite(
      startIndexValue,
    ) &&
    startIndexValue >= 0
      ? startIndexValue
      : calculatedStartIndex;


  const endIndexValue =
    Number(data.end_index);

  const calculatedEndIndex =
    total > 0
      ? Math.min(
          normalizedPage *
            normalizedPageSize,
          total,
        )
      : 0;

  const endIndex =
    Number.isFinite(
      endIndexValue,
    ) &&
    endIndexValue >= 0
      ? endIndexValue
      : calculatedEndIndex;


  return {
    ...data,

    items:
      Array.isArray(data.items)
        ? data.items
        : [],

    total,

    page:
      normalizedPage,

    page_size:
      normalizedPageSize,

    total_pages:
      Math.max(
        1,
        totalPages,
      ),

    start_index:
      startIndex,

    end_index:
      endIndex,

    has_previous:
      normalizedPage > 1,

    has_next:
      normalizedPage <
      Math.max(
        1,
        totalPages,
      ),
  };
}


// ============================================================
// ERROR HANDLING
// ============================================================

function getErrorMessage(
  error,
  fallbackMessage,
) {
  return (
    error?.details?.error?.message ||
    error?.details?.detail ||
    error?.details?.message ||
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    fallbackMessage
  );
}


function createServiceError(
  error,
  fallbackMessage,
) {
  const serviceError =
    new Error(
      getErrorMessage(
        error,
        fallbackMessage,
      ),
    );

  serviceError.status =
    error?.status ??
    error?.response?.status ??
    null;

  serviceError.details =
    error?.details ??
    error?.response?.data ??
    null;

  serviceError.cause =
    error;

  return serviceError;
}


// ============================================================
// GROUND-TRUTH VALIDATION
// ============================================================

function isValidGroundTruthLabel(
  value,
) {
  return (
    value ===
      EMAIL_GROUND_TRUTH_LABELS.NORMAL ||
    value ===
      EMAIL_GROUND_TRUTH_LABELS.BOMBING
  );
}


// ============================================================
// SOURCE VALIDATION
// ============================================================

function isValidEmailSource(
  value,
) {
  return Object.values(
    EMAIL_SOURCES,
  ).includes(value);
}


// ============================================================
// EMAIL LIST
// ============================================================

/**
 * Fetch emails from Email Management.
 *
 * Supported filters:
 *
 *   search
 *   source
 *   status
 *   from_date
 *   to_date
 *
 * Backend applies filters using AND logic.
 */
async function listEmails({
  page = DEFAULT_PAGE,
  pageSize = DEFAULT_PAGE_SIZE,

  search = null,
  source = null,
  status = null,

  fromDate = null,
  toDate = null,
} = {}) {
  const numericPage =
    Number(page);

  const normalizedPage =
    Number.isFinite(
      numericPage,
    )
      ? Math.max(
          1,
          Math.floor(
            numericPage,
          ),
        )
      : DEFAULT_PAGE;


  const numericPageSize =
    Number(pageSize);

  const normalizedPageSize =
    Number.isFinite(
      numericPageSize,
    )
      ? Math.min(
          MAX_PAGE_SIZE,
          Math.max(
            1,
            Math.floor(
              numericPageSize,
            ),
          ),
        )
      : DEFAULT_PAGE_SIZE;


  const normalizedSearch =
    typeof search === "string"
      ? search.trim()
      : "";


  const normalizedSource =
    isValidEmailSource(source)
      ? source
      : null;


  const normalizedStatus =
    isValidGroundTruthLabel(
      status,
    )
      ? status
      : null;


  const params = {
    page:
      normalizedPage,

    page_size:
      normalizedPageSize,

    search:
      normalizedSearch,

    source:
      normalizedSource,

    status:
      normalizedStatus,

    from_date:
      fromDate || null,

    to_date:
      toDate || null,
  };


  try {
    const response =
      await apiClient.get(
        `${EMAIL_BASE_PATH}${buildQueryString(
          params,
        )}`,
      );

    return normalizePaginationResponse(
      response.data,
      {
        page:
          normalizedPage,

        pageSize:
          normalizedPageSize,
      },
    );
  } catch (error) {
    throw createServiceError(
      error,
      "Failed to load emails.",
    );
  }
}


// ============================================================
// EMAIL DETAIL
// ============================================================

/**
 * Fetch one email by UUID.
 *
 * Used by the right-side Email Details drawer.
 */
async function getEmail(
  emailId,
) {
  if (!emailId) {
    throw new Error(
      "Email ID is required.",
    );
  }

  try {
    const response =
      await apiClient.get(
        `${EMAIL_BASE_PATH}/${encodeURIComponent(
          emailId,
        )}`,
      );

    return response.data;
  } catch (error) {
    throw createServiceError(
      error,
      "Failed to load email details.",
    );
  }
}


// ============================================================
// EMAIL STATISTICS
// ============================================================

/**
 * Fetch Email Management statistics.
 *
 * Returns:
 *
 *   total_emails
 *   normal_emails
 *   bombing_emails
 */
async function getEmailStatistics() {
  try {
    const response =
      await apiClient.get(
        `${EMAIL_BASE_PATH}/statistics`,
      );

    return response.data;
  } catch (error) {
    throw createServiceError(
      error,
      "Failed to load email statistics.",
    );
  }
}


// ============================================================
// RAW EMAIL INGESTION
// ============================================================

/**
 * Ingest one raw email.
 *
 * Backend source:
 *
 *   RAW_EMAIL
 *
 * Required:
 *
 *   rawContent
 *   groundTruthLabel
 *
 * Optional:
 *
 *   sourceIdentifier
 */
async function ingestEmail({
  sourceIdentifier = null,
  groundTruthLabel,
  rawContent,
}) {
  if (
    !rawContent ||
    !String(
      rawContent,
    ).trim()
  ) {
    throw new Error(
      "Raw email content is required.",
    );
  }


  if (
    !isValidGroundTruthLabel(
      groundTruthLabel,
    )
  ) {
    throw new Error(
      "A valid ground-truth label is required.",
    );
  }


  const normalizedSourceIdentifier =
    sourceIdentifier ===
      undefined ||
    sourceIdentifier === null
      ? null
      : String(
          sourceIdentifier,
        ).trim();


  if (
    normalizedSourceIdentifier &&
    normalizedSourceIdentifier.length >
      512
  ) {
    throw new Error(
      "Source identifier must not exceed 512 characters.",
    );
  }


  try {
    const response =
      await apiClient.post(
        `${EMAIL_BASE_PATH}/ingest`,
        {
          source_identifier:
            normalizedSourceIdentifier ||
            null,

          ground_truth_label:
            groundTruthLabel,

          raw_content:
            rawContent,
        },
      );

    return response.data;
  } catch (error) {
    throw createServiceError(
      error,
      "Failed to ingest email.",
    );
  }
}


// ============================================================
// SINGLE .EML UPLOAD
// ============================================================

/**
 * Upload one .eml file.
 *
 * Required:
 *
 *   file
 *   groundTruthLabel
 *
 * Backend receives ground_truth_label as a query parameter.
 */
async function uploadEmail(
  file,
  groundTruthLabel,
) {
  if (!file) {
    throw new Error(
      "An email file is required.",
    );
  }


  const fileName =
    typeof file.name === "string"
      ? file.name
          .trim()
          .toLowerCase()
      : "";


  if (
    !fileName.endsWith(
      ".eml",
    )
  ) {
    throw new Error(
      "Only .eml email files are supported.",
    );
  }


  if (
    !isValidGroundTruthLabel(
      groundTruthLabel,
    )
  ) {
    throw new Error(
      "A valid ground-truth label is required.",
    );
  }


  const formData =
    new FormData();

  formData.append(
    "file",
    file,
  );


  try {
    const response =
      await apiClient.post(
        `${EMAIL_BASE_PATH}/upload${buildQueryString(
          {
            ground_truth_label:
              groundTruthLabel,
          },
        )}`,
        formData,
      );

    return response.data;
  } catch (error) {
    throw createServiceError(
      error,
      "Failed to upload email.",
    );
  }
}


// ============================================================
// BULK .EML UPLOAD
// ============================================================

/**
 * Upload multiple .eml files in one batch.
 *
 * Every file receives the same ground-truth label.
 */
async function uploadEmailsBulk(
  files,
  groundTruthLabel,
) {
  if (
    !Array.isArray(files) ||
    files.length === 0
  ) {
    throw new Error(
      "At least one email file is required.",
    );
  }


  if (
    !isValidGroundTruthLabel(
      groundTruthLabel,
    )
  ) {
    throw new Error(
      "A valid ground-truth label is required.",
    );
  }


  for (
    const file of files
  ) {
    const fileName =
      typeof file?.name === "string"
        ? file.name
            .trim()
            .toLowerCase()
        : "";


    if (
      !fileName.endsWith(
        ".eml",
      )
    ) {
      throw new Error(
        `Only .eml files are supported. Invalid file: ${
          file?.name ||
          "unknown"
        }`,
      );
    }
  }


  const formData =
    new FormData();


  files.forEach(
    (file) => {
      formData.append(
        "files",
        file,
      );
    },
  );


  try {
    const response =
      await apiClient.post(
        `${EMAIL_BASE_PATH}/upload/bulk${buildQueryString(
          {
            ground_truth_label:
              groundTruthLabel,
          },
        )}`,
        formData,
      );

    return response.data;
  } catch (error) {
    throw createServiceError(
      error,
      "Failed to upload email batch.",
    );
  }
}


// ============================================================
// FILTER NORMALIZATION
// ============================================================

/**
 * Normalize Email Management filters.
 *
 * UI filters:
 *
 *   Search
 *   Source
 *   Status
 *   From
 *   To
 *
 * No Apply button is required.
 *
 * The caller can invoke listEmails() whenever a filter
 * changes.
 */
function normalizeEmailFilters({
  search = "",
  source = null,
  status = null,
  fromDate = null,
  toDate = null,
} = {}) {
  return {
    search:
      typeof search === "string"
        ? search.trim()
        : "",

    source:
      isValidEmailSource(
        source,
      )
        ? source
        : null,

    status:
      isValidGroundTruthLabel(
        status,
      )
        ? status
        : null,

    fromDate:
      fromDate || null,

    toDate:
      toDate || null,
  };
}


// ============================================================
// PAGINATION NORMALIZATION — PUBLIC HELPER
// ============================================================

function normalizeEmailPagination(
  response,
  options = {},
) {
  return normalizePaginationResponse(
    response,
    options,
  );
}


// ============================================================
// ERROR MESSAGE — PUBLIC HELPER
// ============================================================

function getEmailServiceErrorMessage(
  error,
  fallbackMessage = "Email operation failed.",
) {
  return getErrorMessage(
    error,
    fallbackMessage,
  );
}


// ============================================================
// PUBLIC SERVICE
// ============================================================

const emailService =
  Object.freeze({
    listEmails,

    getEmail,

    getEmailStatistics,

    ingestEmail,

    uploadEmail,

    uploadEmailsBulk,

    normalizeEmailFilters,

    normalizeEmailPagination,

    getEmailServiceErrorMessage,
  });


export default emailService;
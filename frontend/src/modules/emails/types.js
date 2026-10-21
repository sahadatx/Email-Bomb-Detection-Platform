// ============================================================
// EMAIL MODULE TYPES
// ============================================================
//
// Module 02 — Email Collection & Ingestion
//
// Ground truth is assigned during ingestion.
// It is NOT an ML prediction.
//
// Active email sources:
//   - File Upload
//   - Raw Email
//
// IMAP is intentionally excluded from the active frontend
// contract.
//
// ============================================================


// ============================================================
// EMAIL SOURCES
// ============================================================

export const EMAIL_SOURCES = Object.freeze({
  FILE_UPLOAD: "file_upload",
  RAW_EMAIL: "raw_email",
});


// ============================================================
// GROUND-TRUTH LABELS
// ============================================================
//
// These labels are supplied by the user during ingestion.
//
// They represent dataset ground truth:
//
//   NORMAL
//   BOMBING
//
// They are NOT:
//
//   - ML predictions
//   - confidence
//   - risk score
//   - threat level
//
// ============================================================

export const EMAIL_GROUND_TRUTH_LABELS =
  Object.freeze({
    NORMAL: "normal",
    BOMBING: "bombing",
  });


// ============================================================
// INTERNAL EMAIL INGESTION STATUSES
// ============================================================
//
// These represent the internal ingestion lifecycle.
//
// UI Status is different.
//
// UI Status:
//   NORMAL
//   BOMBING
//
// Internal ingestion status:
//   INGESTED
//   FAILED
//
// ============================================================

export const EMAIL_STATUSES =
  Object.freeze({
    INGESTED: "ingested",
    FAILED: "failed",
  });


// ============================================================
// PAGINATION
// ============================================================

export const EMAIL_PAGINATION =
  Object.freeze({
    DEFAULT_PAGE: 1,
    DEFAULT_PAGE_SIZE: 30,
    MAX_PAGE_SIZE: 100,
  });


// ============================================================
// GROUND-TRUTH OPTIONS
// ============================================================
//
// Used by:
//
//   - Add Emails drawer
//   - Upload .EML
//   - Raw Email
//   - Status filter
//
// ============================================================

export const EMAIL_GROUND_TRUTH_OPTIONS =
  Object.freeze([
    Object.freeze({
      value:
        EMAIL_GROUND_TRUTH_LABELS.NORMAL,
      label: "Normal",
    }),

    Object.freeze({
      value:
        EMAIL_GROUND_TRUTH_LABELS.BOMBING,
      label: "Bombing",
    }),
  ]);


// ============================================================
// EMAIL SOURCE OPTIONS
// ============================================================
//
// Used by the Email Management Source filter.
//
// ============================================================

export const EMAIL_SOURCE_OPTIONS =
  Object.freeze([
    Object.freeze({
      value:
        EMAIL_SOURCES.FILE_UPLOAD,
      label: "File Upload",
    }),

    Object.freeze({
      value:
        EMAIL_SOURCES.RAW_EMAIL,
      label: "Raw Email",
    }),
  ]);


// ============================================================
// EMAIL STATUS OPTIONS
// ============================================================
//
// IMPORTANT:
//
// The Email Management "Status" filter represents
// ground truth, not internal ingestion lifecycle.
//
// Therefore:
//
//   NORMAL
//   BOMBING
//
// ============================================================

export const EMAIL_STATUS_OPTIONS =
  Object.freeze([
    Object.freeze({
      value:
        EMAIL_GROUND_TRUTH_LABELS.NORMAL,
      label: "Normal",
    }),

    Object.freeze({
      value:
        EMAIL_GROUND_TRUTH_LABELS.BOMBING,
      label: "Bombing",
    }),
  ]);


// ============================================================
// EMAIL DETAIL FIELD NAMES
// ============================================================
//
// Canonical backend/frontend field names used by the
// Email Details drawer.
//
// ============================================================

export const EMAIL_DETAIL_FIELDS =
  Object.freeze({
    ID: "id",

    GROUND_TRUTH_LABEL:
      "ground_truth_label",

    SOURCE:
      "source",

    SOURCE_IDENTIFIER:
      "source_identifier",

    SUBJECT:
      "subject",

    SENDER:
      "sender",

    RECIPIENTS:
      "recipients",

    CC:
      "cc",

    BCC:
      "bcc",

    REPLY_TO:
      "reply_to",

    MESSAGE_ID:
      "message_id",

    RECEIVED_AT:
      "received_at",

    COLLECTED_AT:
      "collected_at",

    CONTENT_TYPE:
      "content_type",

    MIME_VERSION:
      "mime_version",

    CONTENT_HASH:
      "content_hash",

    RAW_CONTENT:
      "raw_content",

    STATUS:
      "status",

    CREATED_AT:
      "created_at",

    UPDATED_AT:
      "updated_at",
  });


// ============================================================
// EMAIL LIST FIELD NAMES
// ============================================================
//
// Fields returned by the Email Management list endpoint.
//
// ============================================================

export const EMAIL_LIST_FIELDS =
  Object.freeze({
    ID: "id",

    SOURCE:
      "source",

    SOURCE_IDENTIFIER:
      "source_identifier",

    GROUND_TRUTH_LABEL:
      "ground_truth_label",

    MESSAGE_ID:
      "message_id",

    SENDER:
      "sender",

    RECIPIENTS:
      "recipients",

    SUBJECT:
      "subject",

    CONTENT_HASH:
      "content_hash",

    RECEIVED_AT:
      "received_at",

    COLLECTED_AT:
      "collected_at",

    STATUS:
      "status",

    CREATED_AT:
      "created_at",

    UPDATED_AT:
      "updated_at",
  });


// ============================================================
// EMAIL SOURCE VALIDATION
// ============================================================

export function isEmailSource(
  value,
) {
  return Object.values(
    EMAIL_SOURCES,
  ).includes(value);
}


// ============================================================
// GROUND-TRUTH VALIDATION
// ============================================================

export function isEmailGroundTruthLabel(
  value,
) {
  return Object.values(
    EMAIL_GROUND_TRUTH_LABELS,
  ).includes(value);
}


// ============================================================
// INTERNAL STATUS VALIDATION
// ============================================================

export function isEmailStatus(
  value,
) {
  return Object.values(
    EMAIL_STATUSES,
  ).includes(value);
}


// ============================================================
// SOURCE DISPLAY LABEL
// ============================================================

export function getEmailSourceLabel(
  source,
) {
  const labels = {
    [EMAIL_SOURCES.FILE_UPLOAD]:
      "File Upload",

    [EMAIL_SOURCES.RAW_EMAIL]:
      "Raw Email",
  };

  return (
    labels[source] ??
    source ??
    "Unknown"
  );
}


// ============================================================
// GROUND-TRUTH DISPLAY LABEL
// ============================================================

export function getEmailGroundTruthLabel(
  label,
) {
  const labels = {
    [EMAIL_GROUND_TRUTH_LABELS.NORMAL]:
      "Normal",

    [EMAIL_GROUND_TRUTH_LABELS.BOMBING]:
      "Bombing",
  };

  return (
    labels[label] ??
    label ??
    "Unknown"
  );
}


// ============================================================
// INTERNAL STATUS DISPLAY LABEL
// ============================================================

export function getEmailStatusLabel(
  status,
) {
  const labels = {
    [EMAIL_STATUSES.INGESTED]:
      "Ingested",

    [EMAIL_STATUSES.FAILED]:
      "Failed",
  };

  return (
    labels[status] ??
    status ??
    "Unknown"
  );
}


// ============================================================
// SOURCE HELPERS
// ============================================================

export function isFileUploadSource(
  source,
) {
  return (
    source ===
    EMAIL_SOURCES.FILE_UPLOAD
  );
}


export function isRawEmailSource(
  source,
) {
  return (
    source ===
    EMAIL_SOURCES.RAW_EMAIL
  );
}


// ============================================================
// GROUND-TRUTH HELPERS
// ============================================================

export function isNormalEmail(
  label,
) {
  return (
    label ===
    EMAIL_GROUND_TRUTH_LABELS.NORMAL
  );
}


export function isBombingEmail(
  label,
) {
  return (
    label ===
    EMAIL_GROUND_TRUTH_LABELS.BOMBING
  );
}


// ============================================================
// EMAIL OBJECT HELPERS
// ============================================================
//
// These helpers provide safe access to the final Email
// Management response contract.
//
// ============================================================


export function hasEmailDetail(
  email,
) {
  return Boolean(
    email &&
      typeof email === "object",
  );
}


export function hasEmailContent(
  email,
) {
  return Boolean(
    email?.raw_content,
  );
}


export function hasEmailMessageId(
  email,
) {
  return Boolean(
    email?.message_id,
  );
}


export function hasEmailSourceIdentifier(
  email,
) {
  return Boolean(
    email?.source_identifier,
  );
}


// ============================================================
// EMAIL CONTENT HELPERS
// ============================================================

export function getEmailContentType(
  email,
) {
  return (
    email?.content_type ??
    null
  );
}


export function getEmailMimeVersion(
  email,
) {
  return (
    email?.mime_version ??
    null
  );
}


export function getEmailContentHash(
  email,
) {
  return (
    email?.content_hash ??
    null
  );
}


// ============================================================
// EMAIL PARTICIPANT HELPERS
// ============================================================

export function getEmailSender(
  email,
) {
  return (
    email?.sender ??
    null
  );
}


export function getEmailRecipients(
  email,
) {
  return (
    email?.recipients ??
    null
  );
}


export function getEmailCc(
  email,
) {
  return (
    email?.cc ??
    null
  );
}


export function getEmailBcc(
  email,
) {
  return (
    email?.bcc ??
    null
  );
}


export function getEmailReplyTo(
  email,
) {
  return (
    email?.reply_to ??
    null
  );
}


// ============================================================
// EMAIL DATE HELPERS
// ============================================================

export function getEmailReceivedAt(
  email,
) {
  return (
    email?.received_at ??
    null
  );
}


export function getEmailCollectedAt(
  email,
) {
  return (
    email?.collected_at ??
    null
  );
}


// ============================================================
// EMAIL IDENTIFIER HELPERS
// ============================================================

export function getEmailId(
  email,
) {
  return (
    email?.id ??
    null
  );
}


export function getEmailMessageId(
  email,
) {
  return (
    email?.message_id ??
    null
  );
}


// ============================================================
// GROUND-TRUTH BADGE CLASS
// ============================================================
//
// Keeps UI badge styling consistent.
//
// ============================================================

export function getEmailGroundTruthClass(
  label,
) {
  if (
    label ===
    EMAIL_GROUND_TRUTH_LABELS.NORMAL
  ) {
    return "email-status-normal";
  }

  if (
    label ===
    EMAIL_GROUND_TRUTH_LABELS.BOMBING
  ) {
    return "email-status-bombing";
  }

  return "email-status-unknown";
}


// ============================================================
// SOURCE BADGE CLASS
// ============================================================

export function getEmailSourceClass(
  source,
) {
  if (
    source ===
    EMAIL_SOURCES.FILE_UPLOAD
  ) {
    return "email-source-file";
  }

  if (
    source ===
    EMAIL_SOURCES.RAW_EMAIL
  ) {
    return "email-source-raw";
  }

  return "email-source-unknown";
}


// ============================================================
// SAFE DISPLAY VALUE
// ============================================================
//
// Centralized fallback for optional Email Details fields.
//
// ============================================================

export function getEmailDisplayValue(
  value,
  fallback = "—",
) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return fallback;
  }

  return String(value);
}


// ============================================================
// SAFE RECIPIENT DISPLAY
// ============================================================

export function getEmailRecipientsDisplay(
  value,
  fallback = "—",
) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return fallback;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return fallback;
    }

    return value.join(", ");
  }

  return String(value);
}
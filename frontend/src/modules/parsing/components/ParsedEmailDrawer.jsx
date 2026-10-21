import { useEffect } from "react";

import EmailIdentity from "./EmailIdentity";
import HeaderAnalysis from "./HeaderAnalysis";
import AddressAnalysis from "./AddressAnalysis";
import MimeStructure from "./MimeStructure";
import ContentInspector from "./ContentInspector";
import AttachmentList from "./AttachmentList";
import ValidationResult from "./ValidationResult";
import PipelineStatus from "./PipelineStatus";

import {
  EMAIL_LEVEL,
  EMAIL_SOURCE,
  PARSING_STATUS,
} from "../types";



/* ============================================================================
 * DISPLAY HELPERS
 * ========================================================================== */

function displayValue(value) {
  if (
    value === undefined ||
    value === null ||
    value === ""
  ) {
    return "—";
  }

  return String(value);
}



function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}



/* ============================================================================
 * LEVEL
 * ========================================================================== */

function getLevelLabel(level) {
  switch (level) {
    case EMAIL_LEVEL.NORMAL:
      return "Normal";

    case EMAIL_LEVEL.BOMBING:
      return "Bombing";

    default:
      return "—";
  }
}



function getLevelClass(level) {
  switch (level) {
    case EMAIL_LEVEL.NORMAL:
      return "parsing-level parsing-level--normal";

    case EMAIL_LEVEL.BOMBING:
      return "parsing-level parsing-level--bombing";

    default:
      return "parsing-level";
  }
}



/* ============================================================================
 * SOURCE
 * ========================================================================== */

function getSourceLabel(source) {
  switch (source) {
    case EMAIL_SOURCE.RAW_EMAIL:
      return "Raw Email";

    case EMAIL_SOURCE.FILE_UPLOAD:
      return "File Upload";

    case EMAIL_SOURCE.IMAP:
      return "IMAP";

    default:
      if (!source) {
        return "—";
      }

      return String(source)
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) =>
          character.toUpperCase(),
        );
  }
}



function getSourceClass(source) {
  switch (source) {
    case EMAIL_SOURCE.RAW_EMAIL:
      return "parsing-source-badge parsing-source-badge--raw";

    case EMAIL_SOURCE.FILE_UPLOAD:
      return "parsing-source-badge parsing-source-badge--file";

    case EMAIL_SOURCE.IMAP:
      return "parsing-source-badge parsing-source-badge--imap";

    default:
      return "parsing-source-badge";
  }
}



/* ============================================================================
 * PARSING STATUS
 * ========================================================================== */

function getParsingStatusLabel(status) {
  switch (status) {
    case PARSING_STATUS.PARSED:
      return "Parsed";

    case PARSING_STATUS.WARNING:
      return "Warning";

    case PARSING_STATUS.FAILED:
      return "Failed";

    case PARSING_STATUS.PENDING:
    default:
      return "Pending";
  }
}



function getParsingStatusClass(status) {
  switch (status) {
    case PARSING_STATUS.PARSED:
      return "parsing-status-badge parsing-status-badge--parsed";

    case PARSING_STATUS.WARNING:
      return "parsing-status-badge parsing-status-badge--warning";

    case PARSING_STATUS.FAILED:
      return "parsing-status-badge parsing-status-badge--failed";

    case PARSING_STATUS.PENDING:
    default:
      return "parsing-status-badge parsing-status-badge--pending";
  }
}



/* ============================================================================
 * DRAWER HEADER
 * ========================================================================== */

function DrawerHeader({ onClose }) {
  return (
    <header className="parsing-drawer-header">
      <div className="parsing-drawer-header-content">
        <span className="parsing-drawer-eyebrow">
          PARSED EMAIL DETAILS
        </span>

        <h2
          id="parsed-email-drawer-title"
          className="parsing-drawer-title"
        >
          Parsed Email Details
        </h2>

        <p className="parsing-drawer-subtitle">
          Review the parsed email structure, headers,
          content, MIME information, and validation results.
        </p>
      </div>

      <button
        type="button"
        className="parsing-drawer-close"
        onClick={onClose}
        aria-label="Close parsed email drawer"
      >
        ×
      </button>
    </header>
  );
}



/* ============================================================================
 * EMAIL METADATA
 * ========================================================================== */

function EmailMetadata({ email }) {
  const level = email?.level ?? null;
  const source = email?.source ?? null;

  const parsingStatus =
    email?.parsing?.status ??
    PARSING_STATUS.PENDING;

  return (
    <section className="parsing-drawer-metadata">
      <div className="parsing-drawer-metadata-grid">

        <div className="parsing-drawer-metadata-item">
          <span className="parsing-drawer-metadata-label">
            Level
          </span>

          <span className={getLevelClass(level)}>
            {getLevelLabel(level)}
          </span>
        </div>


        <div className="parsing-drawer-metadata-item">
          <span className="parsing-drawer-metadata-label">
            Source
          </span>

          <span className={getSourceClass(source)}>
            {getSourceLabel(source)}
          </span>
        </div>


        <div className="parsing-drawer-metadata-item">
          <span className="parsing-drawer-metadata-label">
            Parsing Status
          </span>

          <span
            className={getParsingStatusClass(
              parsingStatus,
            )}
          >
            {getParsingStatusLabel(
              parsingStatus,
            )}
          </span>
        </div>


        <div className="parsing-drawer-metadata-item">
          <span className="parsing-drawer-metadata-label">
            Email ID
          </span>

          <span className="parsing-drawer-metadata-value parsing-drawer-monospace">
            {displayValue(email?.email_id)}
          </span>
        </div>


        <div className="parsing-drawer-metadata-item">
          <span className="parsing-drawer-metadata-label">
            Source Identifier
          </span>

          <span className="parsing-drawer-metadata-value parsing-drawer-monospace">
            {displayValue(
              email?.source_identifier,
            )}
          </span>
        </div>

      </div>
    </section>
  );
}



/* ============================================================================
 * TIME INFORMATION
 * ========================================================================== */

function TimeInformation({ email }) {
  const timestamps =
    email?.timestamps || {};

  return (
    <section className="parsing-drawer-section">
      <div className="parsing-drawer-section-header">
        <span className="parsing-drawer-section-eyebrow">
          TIME
        </span>

        <h3 className="parsing-drawer-section-title">
          Time Information
        </h3>
      </div>

      <dl className="parsing-drawer-detail-list">

        <div className="parsing-drawer-detail-row">
          <dt>Received</dt>
          <dd>
            {formatDate(
              timestamps.received_at,
            )}
          </dd>
        </div>


        <div className="parsing-drawer-detail-row">
          <dt>Collected At</dt>
          <dd>
            {formatDate(
              timestamps.collected_at,
            )}
          </dd>
        </div>


        {timestamps.parsed_at && (
          <div className="parsing-drawer-detail-row">
            <dt>Parsed At</dt>
            <dd>
              {formatDate(
                timestamps.parsed_at,
              )}
            </dd>
          </div>
        )}

      </dl>
    </section>
  );
}



/* ============================================================================
 * PARSING INFORMATION
 * ========================================================================== */

function ParsingInformation({ email }) {
  const parsing =
    email?.parsing || {};

  return (
    <section className="parsing-drawer-section">
      <div className="parsing-drawer-section-header">
        <span className="parsing-drawer-section-eyebrow">
          PARSING
        </span>

        <h3 className="parsing-drawer-section-title">
          Parsing Information
        </h3>
      </div>

      <dl className="parsing-drawer-detail-list">

        <div className="parsing-drawer-detail-row">
          <dt>Status</dt>

          <dd>
            {getParsingStatusLabel(
              parsing.status,
            )}
          </dd>
        </div>


        <div className="parsing-drawer-detail-row">
          <dt>Parser Version</dt>

          <dd className="parsing-drawer-monospace">
            {displayValue(
              parsing.parser_version,
            )}
          </dd>
        </div>


        <div className="parsing-drawer-detail-row">
          <dt>Processing Time</dt>

          <dd>
            {parsing.processing_time_ms !==
              undefined &&
            parsing.processing_time_ms !==
              null
              ? `${parsing.processing_time_ms} ms`
              : "—"}
          </dd>
        </div>

      </dl>
    </section>
  );
}



/* ============================================================================
 * STATES
 * ========================================================================== */

function EmptyState() {
  return (
    <div
      className="parsing-drawer-state"
      role="status"
    >
      <span>
        No parsed email selected.
      </span>
    </div>
  );
}



function LoadingState() {
  return (
    <div
      className="parsing-drawer-state"
      role="status"
      aria-live="polite"
    >
      <div
        className="parsing-loading-indicator"
        aria-hidden="true"
      />

      <span>
        Loading parsed email details...
      </span>
    </div>
  );
}



function ErrorState({ error }) {
  return (
    <div
      className="parsing-drawer-state parsing-drawer-error-state"
      role="alert"
    >
      <strong>
        Failed to load parsed email
      </strong>

      <span>
        {displayValue(error)}
      </span>
    </div>
  );
}



/* ============================================================================
 * PARSED EMAIL CONTENT
 *
 * IMPORTANT:
 * Each child component receives the props it actually expects.
 * ========================================================================== */

function ParsedEmailContent({ email }) {
  if (!email) {
    return <EmptyState />;
  }

  return (
    <div className="parsing-drawer-content">

      {/* ------------------------------------------------------------------
       * Module 03 / Module 02 metadata
       * ---------------------------------------------------------------- */}

      <EmailMetadata
        email={email}
      />


      {/* ------------------------------------------------------------------
       * Identity
       *
       * EmailIdentity expects:
       *     identity
       *     source
       *     sourceIdentifier
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <EmailIdentity
          identity={
            email.identity
          }
          source={
            email.source
          }
          sourceIdentifier={
            email.source_identifier
          }
        />
      </section>


      {/* ------------------------------------------------------------------
       * Address Analysis
       *
       * AddressAnalysis expects the parsed email object.
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <AddressAnalysis
          email={email}
        />
      </section>


      {/* ------------------------------------------------------------------
       * Header Analysis
       *
       * HeaderAnalysis expects:
       *     headers
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <HeaderAnalysis
          headers={
            email.headers
          }
        />
      </section>


      {/* ------------------------------------------------------------------
       * MIME Structure
       *
       * MimeStructure expects:
       *     mimeParts
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <MimeStructure
          mimeParts={
            email.mime_parts
          }
        />
      </section>


      {/* ------------------------------------------------------------------
       * Content Inspector
       *
       * ContentInspector expects:
       *     textBody
       *     htmlBody
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <ContentInspector
          textBody={
            email.text_body
          }
          htmlBody={
            email.html_body
          }
        />
      </section>


      {/* ------------------------------------------------------------------
       * Attachments
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <AttachmentList
          email={email}
        />
      </section>


      {/* ------------------------------------------------------------------
       * Validation
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <ValidationResult
          email={email}
        />
      </section>


      {/* ------------------------------------------------------------------
       * Pipeline
       * ---------------------------------------------------------------- */}

      <section className="parsing-drawer-component-section">
        <PipelineStatus
          email={email}
        />
      </section>


      {/* ------------------------------------------------------------------
       * Time
       * ---------------------------------------------------------------- */}

      <TimeInformation
        email={email}
      />


      {/* ------------------------------------------------------------------
       * Parsing metadata
       * ---------------------------------------------------------------- */}

      <ParsingInformation
        email={email}
      />

    </div>
  );
}



/* ============================================================================
 * DRAWER
 * ========================================================================== */

export default function ParsedEmailDrawer({
  open = false,
  email = null,
  loading = false,
  error = "",
  onClose,
}) {

  /* ------------------------------------------------------------------------
   * Escape key
   * ---------------------------------------------------------------------- */

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose?.();
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [
    open,
    onClose,
  ]);


  /* ------------------------------------------------------------------------
   * Prevent background scrolling
   * ---------------------------------------------------------------------- */

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    return () => {
      document.body.style.overflow =
        previousOverflow;
    };
  }, [open]);


  if (!open) {
    return null;
  }


  return (
    <div
      className="parsing-drawer-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose?.();
        }
      }}
    >

      <aside
        className="parsing-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="parsed-email-drawer-title"
        onMouseDown={(event) => {
          event.stopPropagation();
        }}
      >

        <DrawerHeader
          onClose={onClose}
        />


        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState
            error={error}
          />
        ) : (
          <ParsedEmailContent
            email={email}
          />
        )}

      </aside>

    </div>
  );
}
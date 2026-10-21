import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getParsedEmail } from "../services/parsingService";
import { PARSING_STATUS } from "../types";

import EmailIdentity from "../components/EmailIdentity";
import HeaderAnalysis from "../components/HeaderAnalysis";
import AddressAnalysis from "../components/AddressAnalysis";
import ContentInspector from "../components/ContentInspector";
import MimeStructure from "../components/MimeStructure";
import AttachmentList from "../components/AttachmentList";
import ValidationResult from "../components/ValidationResult";
import PipelineStatus from "../components/PipelineStatus";


// ============================================================
// STATUS
// ============================================================

function getParsingStatus(parsedEmail) {
  return (
    parsedEmail?.parsing?.status ??
    PARSING_STATUS.PENDING
  );
}


function getStatusLabel(status) {
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


function getStatusClass(status) {
  switch (status) {
    case PARSING_STATUS.PARSED:
      return "parsing-status parsing-status--parsed";

    case PARSING_STATUS.WARNING:
      return "parsing-status parsing-status--warning";

    case PARSING_STATUS.FAILED:
      return "parsing-status parsing-status--failed";

    case PARSING_STATUS.PENDING:
    default:
      return "parsing-status parsing-status--pending";
  }
}


// ============================================================
// FORMATTING
// ============================================================

function formatProcessingTime(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "—";
  }

  return `${numericValue.toFixed(2)} ms`;
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


// ============================================================
// PARSED DATA COUNTS
// ============================================================

function getHeaderCount(headers) {
  if (
    !headers ||
    typeof headers !== "object" ||
    Array.isArray(headers)
  ) {
    return 0;
  }

  return Object.keys(headers).length;
}


function getMimePartCount(parsedEmail) {
  if (
    Array.isArray(
      parsedEmail?.mime_parts,
    )
  ) {
    return parsedEmail.mime_parts.length;
  }

  return 0;
}


function getAttachmentCount(parsedEmail) {
  if (
    Array.isArray(
      parsedEmail?.attachments,
    )
  ) {
    return parsedEmail.attachments.length;
  }

  return 0;
}


// ============================================================
// VALIDATION
// ============================================================

function getValidationData(parsedEmail) {
  const errors = Array.isArray(
    parsedEmail?.validation_errors,
  )
    ? parsedEmail.validation_errors
    : [];

  const warnings = Array.isArray(
    parsedEmail?.validation_warnings,
  )
    ? parsedEmail.validation_warnings
    : [];

  return {
    errors,
    warnings,
    is_valid: errors.length === 0,
  };
}


function getValidationState(parsedEmail) {
  const status =
    getParsingStatus(parsedEmail);

  const errors =
    Array.isArray(
      parsedEmail?.validation_errors,
    )
      ? parsedEmail.validation_errors
      : [];

  if (
    errors.length > 0
  ) {
    return false;
  }

  if (
    status === PARSING_STATUS.FAILED
  ) {
    return false;
  }

  return true;
}


// ============================================================
// COMPONENT
// ============================================================

export default function ParsedEmail() {
  const { emailId } = useParams();

  const navigate = useNavigate();

  const [
    parsedEmail,
    setParsedEmail,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  // ==========================================================
  // LOAD PERSISTED PARSED EMAIL
  // ==========================================================

  const loadParsedEmail =
    useCallback(
      async (signal) => {
        if (!emailId) {
          setError(
            "Email ID is missing.",
          );

          setLoading(false);

          return;
        }

        setLoading(true);
        setError("");

        try {
          const response =
            await getParsedEmail(
              emailId,
              {
                signal,
              },
            );

          setParsedEmail(
            response,
          );
        } catch (
          requestError
        ) {
          if (
            requestError?.name ===
            "AbortError"
          ) {
            return;
          }

          if (
            requestError?.response
              ?.status === 404 ||
            requestError?.status === 404
          ) {
            setError(
              "No persisted parsing result was found for this email.",
            );
          } else {
            setError(
              requestError?.message ||
                "Failed to load parsed email.",
            );
          }

          setParsedEmail(null);
        } finally {
          if (!signal?.aborted) {
            setLoading(false);
          }
        }
      },
      [emailId],
    );


  // ==========================================================
  // LOAD EFFECT
  // ==========================================================

  useEffect(() => {
    const controller =
      new AbortController();

    loadParsedEmail(
      controller.signal,
    );

    return () => {
      controller.abort();
    };
  }, [
    loadParsedEmail,
  ]);


  // ==========================================================
  // BACK
  // ==========================================================

  const handleBack =
    useCallback(() => {
      navigate("/parsing");
    }, [navigate]);


  // ==========================================================
  // DERIVED DATA
  // ==========================================================

  const status =
    getParsingStatus(
      parsedEmail,
    );

  const identity =
    parsedEmail?.identity ?? {};

  const timestamps =
    parsedEmail?.timestamps ?? {};

  const parsing =
    parsedEmail?.parsing ?? {};

  const validation =
    useMemo(
      () =>
        getValidationData(
          parsedEmail,
        ),
      [parsedEmail],
    );

  const subject =
    identity.subject ||
    "(No subject)";

  const validationIsValid =
    getValidationState(
      parsedEmail,
    );

  const headerCount =
    getHeaderCount(
      parsedEmail?.headers,
    );

  const mimePartCount =
    getMimePartCount(
      parsedEmail,
    );

  const attachmentCount =
    getAttachmentCount(
      parsedEmail,
    );


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <section className="parsed-email-page">
        <div
          className="parsed-email-state"
          role="status"
          aria-live="polite"
        >
          <span
            className="parsing-loading-indicator"
            aria-hidden="true"
          />

          <strong>
            Loading parsed email...
          </strong>

          <span>
            Retrieving persisted parsing
            results and normalized email
            data.
          </span>
        </div>
      </section>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error) {
    return (
      <section className="parsed-email-page">

        <button
          type="button"
          className="parsing-button parsing-button--secondary"
          onClick={handleBack}
        >
          ← Back to Parsing Workspace
        </button>

        <div
          className="parsing-alert parsing-alert--error"
          role="alert"
        >
          {error}
        </div>

      </section>
    );
  }


  // ==========================================================
  // EMPTY
  // ==========================================================

  if (!parsedEmail) {
    return (
      <section className="parsed-email-page">

        <button
          type="button"
          className="parsing-button parsing-button--secondary"
          onClick={handleBack}
        >
          ← Back to Parsing Workspace
        </button>

        <div className="parsed-email-state">
          <strong>
            No parsing data available.
          </strong>

          <span>
            This email has not been parsed
            yet.
          </span>
        </div>

      </section>
    );
  }


  // ==========================================================
  // PAGE
  // ==========================================================

  return (
    <section className="parsed-email-page">

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <header className="parsed-email-page__header">

        <button
          type="button"
          className="parsing-button parsing-button--secondary"
          onClick={handleBack}
        >
          ← Back to Parsing Workspace
        </button>


        <div className="parsed-email-page__heading">

          <div>

            <h1>
              {subject}
            </h1>

            <p>
              Parsed, normalized and
              validated representation
              of the collected email.
            </p>

          </div>


          <div className="parsed-email-page__badges">

            <span
              className={getStatusClass(
                status,
              )}
            >
              {getStatusLabel(
                status,
              )}
            </span>


            <span
              className={
                validationIsValid
                  ? "parsing-validation-badge parsing-validation-badge--valid"
                  : "parsing-validation-badge parsing-validation-badge--invalid"
              }
            >
              {validationIsValid
                ? "Valid"
                : "Validation Issues"}
            </span>

          </div>

        </div>

      </header>


      {/* ================================================== */}
      {/* METADATA */}
      {/* ================================================== */}

      <section className="parsed-email-metadata">

        <article className="parsed-email-metadata__item">
          <span>
            Parser Version
          </span>

          <strong>
            {parsing.parser_version ||
              "—"}
          </strong>
        </article>


        <article className="parsed-email-metadata__item">
          <span>
            Processing Time
          </span>

          <strong>
            {formatProcessingTime(
              parsing.processing_time_ms,
            )}
          </strong>
        </article>


        <article className="parsed-email-metadata__item">
          <span>
            Received
          </span>

          <strong>
            {formatDate(
              timestamps.received_at,
            )}
          </strong>
        </article>


        <article className="parsed-email-metadata__item">
          <span>
            Collected
          </span>

          <strong>
            {formatDate(
              timestamps.collected_at,
            )}
          </strong>
        </article>


        <article className="parsed-email-metadata__item">
          <span>
            Parsed
          </span>

          <strong>
            {formatDate(
              timestamps.parsed_at,
            )}
          </strong>
        </article>

      </section>


      {/* ================================================== */}
      {/* SUMMARY */}
      {/* ================================================== */}

      <section className="parsed-email-summary">

        <article className="parsed-email-summary__card">
          <span>
            Headers
          </span>

          <strong>
            {headerCount}
          </strong>
        </article>


        <article className="parsed-email-summary__card">
          <span>
            MIME Parts
          </span>

          <strong>
            {mimePartCount}
          </strong>
        </article>


        <article className="parsed-email-summary__card">
          <span>
            Attachments
          </span>

          <strong>
            {attachmentCount}
          </strong>
        </article>


        <article className="parsed-email-summary__card">
          <span>
            Validation
          </span>

          <strong>
            {validationIsValid
              ? "Valid"
              : "Issues"}
          </strong>
        </article>

      </section>


      {/* ================================================== */}
      {/* IDENTITY */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <EmailIdentity
          identity={identity}
          source={
            parsedEmail.source
          }
          sourceIdentifier={
            parsedEmail.source_identifier
          }
        />

      </section>


      {/* ================================================== */}
      {/* HEADER ANALYSIS */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <HeaderAnalysis
          headers={
            parsedEmail.headers ??
            {}
          }
        />

      </section>


      {/* ================================================== */}
      {/* ADDRESS ANALYSIS */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <AddressAnalysis
          identity={identity}
        />

      </section>


      {/* ================================================== */}
      {/* CONTENT */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <ContentInspector
          textBody={
            parsedEmail.text_body
          }
          htmlBody={
            parsedEmail.html_body
          }
        />

      </section>


      {/* ================================================== */}
      {/* MIME STRUCTURE */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <MimeStructure
          mimeParts={
            parsedEmail.mime_parts ??
            []
          }
        />

      </section>


      {/* ================================================== */}
      {/* ATTACHMENTS */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <AttachmentList
          attachments={
            parsedEmail.attachments ??
            []
          }
        />

      </section>


      {/* ================================================== */}
      {/* VALIDATION */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <ValidationResult
          validation={
            validation
          }
        />

      </section>


      {/* ================================================== */}
      {/* PIPELINE */}
      {/* ================================================== */}

      <section className="parsed-email-section">

        <PipelineStatus
          status={status}
          emailId={
            parsedEmail.email_id
          }
        />

      </section>

    </section>
  );
}

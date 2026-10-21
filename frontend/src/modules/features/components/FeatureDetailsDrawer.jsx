import React, {
  useEffect,
} from "react";

import {
  FEATURE_COUNT,
  FEATURE_STATUS,
  getFeatureStatusLabel,
  getFeatureSourceLabel,
  getFeatureLevelLabel,
  getFeatureVectorValues,
  formatFeatureValue,
} from "../types";


// ============================================================
// DISPLAY HELPERS
// ============================================================

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

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "—";
  }

  return date.toLocaleString();
}


// ============================================================
// LEVEL
// ============================================================

function getLevelClass(level) {
  switch (level) {
    case "bombing":
      return (
        "feature-drawer-badge " +
        "feature-drawer-badge--bombing"
      );

    case "normal":
      return (
        "feature-drawer-badge " +
        "feature-drawer-badge--normal"
      );

    default:
      return "feature-drawer-badge";
  }
}


// ============================================================
// SOURCE
// ============================================================

function getSourceClass(source) {
  switch (source) {
    case "file_upload":
      return (
        "feature-drawer-badge " +
        "feature-drawer-badge--file"
      );

    case "raw_email":
      return (
        "feature-drawer-badge " +
        "feature-drawer-badge--raw"
      );

    default:
      return "feature-drawer-badge";
  }
}


// ============================================================
// STATUS
// ============================================================

function getStatusClass(status) {
  switch (status) {
    case FEATURE_STATUS.EXTRACTED:
      return (
        "feature-drawer-status " +
        "feature-drawer-status--extracted"
      );

    case FEATURE_STATUS.WARNING:
      return (
        "feature-drawer-status " +
        "feature-drawer-status--warning"
      );

    case FEATURE_STATUS.FAILED:
      return (
        "feature-drawer-status " +
        "feature-drawer-status--failed"
      );

    case FEATURE_STATUS.PENDING:
    default:
      return (
        "feature-drawer-status " +
        "feature-drawer-status--pending"
      );
  }
}


// ============================================================
// DRAWER HEADER
// ============================================================

function DrawerHeader({
  onClose,
}) {
  return (
    <header
      className="feature-details-drawer__header"
    >
      <div>
        <span
          className="feature-details-drawer__eyebrow"
        >
          FEATURE ENGINEERING
        </span>

        <h2
          id="feature-details-drawer-title"
          className="feature-details-drawer__title"
        >
          Feature Details
        </h2>

        <p
          className="feature-details-drawer__subtitle"
        >
          Review extracted F1-F12 security
          features for this parsed email.
        </p>
      </div>

      <button
        type="button"
        className="feature-details-drawer__close"
        onClick={onClose}
        aria-label="Close feature details drawer"
      >
        ×
      </button>
    </header>
  );
}


// ============================================================
// METADATA
// ============================================================

function FeatureMetadata({
  feature,
}) {
  const identity =
    feature?.identity ?? {};

  const metadata =
    feature?.metadata ?? {};

  const source =
    identity.source;

  const level =
    identity.level;

  const status =
    metadata.status ??
    FEATURE_STATUS.PENDING;

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-grid"
      >

        {/* LEVEL */}

        <div
          className="feature-details-field"
        >
          <span
            className="feature-details-field__label"
          >
            Level
          </span>

          <span
            className={getLevelClass(level)}
          >
            {getFeatureLevelLabel(
              level,
            )}
          </span>
        </div>


        {/* SOURCE */}

        <div
          className="feature-details-field"
        >
          <span
            className="feature-details-field__label"
          >
            Source
          </span>

          <span
            className={getSourceClass(source)}
          >
            {getFeatureSourceLabel(
              source,
            )}
          </span>
        </div>


        {/* STATUS */}

        <div
          className="feature-details-field"
        >
          <span
            className="feature-details-field__label"
          >
            Extraction Status
          </span>

          <span
            className={getStatusClass(
              status,
            )}
          >
            {getFeatureStatusLabel(
              status,
            )}
          </span>
        </div>


        {/* EMAIL ID */}

        <div
          className="feature-details-field"
        >
          <span
            className="feature-details-field__label"
          >
            Email ID
          </span>

          <span
            className={
              "feature-details-field__value " +
              "feature-details-field__value--mono"
            }
          >
            {displayValue(
              identity.emailId,
            )}
          </span>
        </div>


        {/* SOURCE IDENTIFIER */}

        <div
          className="feature-details-field"
        >
          <span
            className="feature-details-field__label"
          >
            Source Identifier
          </span>

          <span
            className={
              "feature-details-field__value " +
              "feature-details-field__value--mono"
            }
          >
            {displayValue(
              identity.sourceIdentifier,
            )}
          </span>
        </div>

      </div>
    </section>
  );
}


// ============================================================
// EMAIL IDENTITY
// ============================================================

function EmailIdentity({
  feature,
}) {
  const identity =
    feature?.identity ?? {};

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-section__header"
      >
        <span
          className="feature-details-section__eyebrow"
        >
          EMAIL
        </span>

        <h3
          className="feature-details-section__title"
        >
          Email Identity
        </h3>
      </div>

      <dl
        className="feature-details-list"
      >

        <div
          className="feature-details-list__row"
        >
          <dt>Subject</dt>

          <dd>
            {displayValue(
              identity.subject,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Sender</dt>

          <dd>
            {displayValue(
              identity.sender,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Message-ID</dt>

          <dd
            className="feature-details-monospace"
          >
            {displayValue(
              identity.messageId,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Source Identifier</dt>

          <dd
            className="feature-details-monospace"
          >
            {displayValue(
              identity.sourceIdentifier,
            )}
          </dd>
        </div>

      </dl>
    </section>
  );
}


// ============================================================
// TIME INFORMATION
// ============================================================

function TimeInformation({
  feature,
}) {
  const timestamps =
    feature?.timestamps ?? {};

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-section__header"
      >
        <span
          className="feature-details-section__eyebrow"
        >
          TIME
        </span>

        <h3
          className="feature-details-section__title"
        >
          Time Information
        </h3>
      </div>

      <dl
        className="feature-details-list"
      >

        <div
          className="feature-details-list__row"
        >
          <dt>Received</dt>

          <dd>
            {formatDate(
              timestamps.receivedAt,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Collected At</dt>

          <dd>
            {formatDate(
              timestamps.collectedAt,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Parsed At</dt>

          <dd>
            {formatDate(
              timestamps.parsedAt,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Extracted At</dt>

          <dd>
            {formatDate(
              timestamps.extractedAt,
            )}
          </dd>
        </div>

      </dl>
    </section>
  );
}


// ============================================================
// FEATURE VECTOR
// ============================================================

function FeatureVectorSection({
  feature,
}) {
  const vector =
    feature?.featureVector ?? {};

  const values =
    getFeatureVectorValues(
      vector,
    );

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-section__header"
      >
        <span
          className="feature-details-section__eyebrow"
        >
          FEATURES
        </span>

        <h3
          className="feature-details-section__title"
        >
          Feature Vector
        </h3>

        <p
          className="feature-details-section__description"
        >
          Canonical F1-F12 extracted values.
        </p>
      </div>


      <div
        className="feature-vector-grid"
      >

        {values.map(
          (item) => (
            <div
              key={
                item.id
              }
              className="feature-vector-item"
            >

              <div
                className="feature-vector-item__header"
              >
                <span
                  className="feature-vector-item__id"
                >
                  {item.id}
                </span>

                <span
                  className="feature-vector-item__type"
                >
                  {item.dataType}
                </span>
              </div>


              <div
                className="feature-vector-item__name"
              >
                {item.name}
              </div>


              <div
                className="feature-vector-item__value"
              >
                {formatFeatureValue(
                  item.value,
                )}
              </div>

            </div>
          ),
        )}

      </div>
    </section>
  );
}


// ============================================================
// FEATURE INFORMATION
// ============================================================

function FeatureInformation({
  feature,
}) {
  const features =
    Array.isArray(
      feature?.features,
    )
      ? feature.features
      : [];

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-section__header"
      >
        <span
          className="feature-details-section__eyebrow"
        >
          DEFINITIONS
        </span>

        <h3
          className="feature-details-section__title"
        >
          Feature Information
        </h3>
      </div>


      <div
        className="feature-information-list"
      >

        {features.length === 0 ? (
          <div
            className="feature-details-empty"
          >
            No individual feature records
            are available.
          </div>
        ) : (
          features.map(
            (item) => (
              <div
                key={
                  item.featureId
                }
                className="feature-information-item"
              >

                <div
                  className="feature-information-item__header"
                >
                  <span
                    className="feature-information-item__id"
                  >
                    {
                      item.featureId
                    }
                  </span>

                  <span
                    className="feature-information-item__name"
                  >
                    {
                      item.featureName
                    }
                  </span>
                </div>


                <div
                  className="feature-information-item__value"
                >
                  {
                    item.displayValue ??
                    formatFeatureValue(
                      item.value,
                    )
                  }
                </div>


                {item.description && (
                  <p
                    className="feature-information-item__description"
                  >
                    {
                      item.description
                    }
                  </p>
                )}

              </div>
            ),
          )
        )}

      </div>
    </section>
  );
}


// ============================================================
// VALIDATION
// ============================================================

function ValidationSection({
  feature,
}) {
  const validation =
    feature?.validation ?? {};

  const errors =
    Array.isArray(
      validation.errors,
    )
      ? validation.errors
      : [];

  const warnings =
    Array.isArray(
      validation.warnings,
    )
      ? validation.warnings
      : [];

  const isValid =
    validation.isValid !== false;

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-section__header"
      >
        <span
          className="feature-details-section__eyebrow"
        >
          VALIDATION
        </span>

        <h3
          className="feature-details-section__title"
        >
          Validation Result
        </h3>
      </div>


      <div
        className={
          "feature-validation " +
          (
            isValid
              ? "feature-validation--valid"
              : "feature-validation--invalid"
          )
        }
      >
        <strong>
          {isValid
            ? "Valid"
            : "Validation Failed"}
        </strong>
      </div>


      {errors.length > 0 && (
        <div
          className="feature-validation-list"
        >
          <strong>
            Errors
          </strong>

          <ul>
            {errors.map(
              (
                error,
                index,
              ) => (
                <li
                  key={index}
                >
                  {error}
                </li>
              ),
            )}
          </ul>
        </div>
      )}


      {warnings.length > 0 && (
        <div
          className="feature-validation-list"
        >
          <strong>
            Warnings
          </strong>

          <ul>
            {warnings.map(
              (
                warning,
                index,
              ) => (
                <li
                  key={index}
                >
                  {warning}
                </li>
              ),
            )}
          </ul>
        </div>
      )}

    </section>
  );
}


// ============================================================
// EXTRACTION METADATA
// ============================================================

function ExtractionMetadata({
  feature,
}) {
  const metadata =
    feature?.metadata ?? {};

  return (
    <section
      className="feature-details-section"
    >
      <div
        className="feature-details-section__header"
      >
        <span
          className="feature-details-section__eyebrow"
        >
          EXTRACTION
        </span>

        <h3
          className="feature-details-section__title"
        >
          Extraction Metadata
        </h3>
      </div>

      <dl
        className="feature-details-list"
      >

        <div
          className="feature-details-list__row"
        >
          <dt>Extractor Version</dt>

          <dd
            className="feature-details-monospace"
          >
            {displayValue(
              metadata.extractorVersion,
            )}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Processing Time</dt>

          <dd>
            {metadata.processingTimeMs !==
              undefined &&
            metadata.processingTimeMs !==
              null
              ? `${metadata.processingTimeMs} ms`
              : "—"}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Feature Count</dt>

          <dd>
            {FEATURE_COUNT}
          </dd>
        </div>


        <div
          className="feature-details-list__row"
        >
          <dt>Extracted At</dt>

          <dd>
            {formatDate(
              metadata.extractedAt,
            )}
          </dd>
        </div>

      </dl>
    </section>
  );
}


// ============================================================
// EMPTY STATE
// ============================================================

function EmptyState() {
  return (
    <div
      className="feature-details-drawer__state"
      role="status"
    >
      <span>
        No feature record selected.
      </span>
    </div>
  );
}


// ============================================================
// LOADING STATE
// ============================================================

function LoadingState() {
  return (
    <div
      className="feature-details-drawer__state"
      role="status"
      aria-live="polite"
    >
      <div
        className="feature-details-loading-indicator"
        aria-hidden="true"
      />

      <span>
        Loading feature details...
      </span>
    </div>
  );
}


// ============================================================
// ERROR STATE
// ============================================================

function ErrorState({
  error,
}) {
  return (
    <div
      className={
        "feature-details-drawer__state " +
        "feature-details-drawer__error"
      }
      role="alert"
    >
      <strong>
        Failed to load feature details
      </strong>

      <span>
        {displayValue(error)}
      </span>
    </div>
  );
}


// ============================================================
// FEATURE CONTENT
// ============================================================

function FeatureContent({
  feature,
}) {
  if (!feature) {
    return (
      <EmptyState />
    );
  }

  return (
    <div
      className="feature-details-drawer__body"
    >

      <FeatureMetadata
        feature={feature}
      />

      <EmailIdentity
        feature={feature}
      />

      <TimeInformation
        feature={feature}
      />

      <FeatureVectorSection
        feature={feature}
      />

      <FeatureInformation
        feature={feature}
      />

      <ValidationSection
        feature={feature}
      />

      <ExtractionMetadata
        feature={feature}
      />

    </div>
  );
}


// ============================================================
// MAIN DRAWER
// ============================================================

export default function FeatureDetailsDrawer({
  open = false,

  feature = null,

  loading = false,

  error = "",

  onClose,
}) {

  // ==========================================================
  // ESCAPE KEY
  // ==========================================================

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    function handleKeyDown(
      event,
    ) {
      if (
        event.key ===
        "Escape"
      ) {
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


  // ==========================================================
  // BACKGROUND SCROLL LOCK
  // ==========================================================

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
  }, [
    open,
  ]);


  if (!open) {
    return null;
  }


  // ==========================================================
  // DRAWER
  // ==========================================================

  return (
    <div
      className="feature-details-drawer__backdrop"
      role="presentation"

      onMouseDown={(
        event,
      ) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose?.();
        }
      }}
    >

      <aside
        className="feature-details-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="feature-details-drawer-title"

        onMouseDown={(
          event,
        ) => {
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
          <FeatureContent
            feature={feature}
          />
        )}

      </aside>

    </div>
  );
}
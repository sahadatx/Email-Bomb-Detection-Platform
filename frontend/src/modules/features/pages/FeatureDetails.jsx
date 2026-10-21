import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import featureService, {
  FeatureApiError,
} from "../services/featureService";

import {
  FEATURE_COUNT,
  FEATURE_DEFINITIONS,
  FEATURE_STATUS,
  getFeatureDefinition,
  getFeatureStatusLabel,
} from "../types";

// ============================================================
// HELPERS
// ============================================================

function getEmailIdFromLocation() {
  const pathname = window.location.pathname || "";

  const parts = pathname
    .split("/")
    .filter(Boolean);

  const featuresIndex = parts.indexOf("features");

  if (
    featuresIndex === -1 ||
    !parts[featuresIndex + 1]
  ) {
    return null;
  }

  return decodeURIComponent(
    parts[featuresIndex + 1],
  );
}

function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatFeatureValue(value, dataType) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (dataType === "boolean") {
    return value ? "True" : "False";
  }

  return String(value);
}

function getStatusClass(status) {
  return status || FEATURE_STATUS.PENDING;
}

// ============================================================
// STATUS BADGE
// ============================================================

function StatusBadge({ status }) {
  return (
    <span
      className={`feature-status-badge feature-status-badge--${getStatusClass(
        status,
      )}`}
    >
      {getFeatureStatusLabel(status)}
    </span>
  );
}

// ============================================================
// LOADING
// ============================================================

function LoadingState() {
  return (
    <div className="feature-details__state">
      Loading feature details…
    </div>
  );
}

// ============================================================
// ERROR
// ============================================================

function ErrorState({ message, onRetry }) {
  return (
    <div className="feature-details__state feature-details__state--error">
      <div className="feature-details__state-title">
        Unable to load feature details
      </div>

      <div className="feature-details__state-message">
        {message}
      </div>

      <button
        type="button"
        className="feature-button feature-button--secondary"
        onClick={onRetry}
      >
        Retry
      </button>
    </div>
  );
}

// ============================================================
// INFORMATION ITEM
// ============================================================

function InformationItem({ label, value }) {
  return (
    <div className="feature-information-item">
      <div className="feature-information-item__label">
        {label}
      </div>

      <div className="feature-information-item__value">
        {value || "—"}
      </div>
    </div>
  );
}

// ============================================================
// FEATURE VALUE ROW
// ============================================================

function FeatureValueRow({ feature }) {
  const definition = getFeatureDefinition(feature.id);

  const dataType =
    definition?.dataType ||
    feature.dataType;

  return (
    <tr>
      <td>
        <strong>{feature.id}</strong>
      </td>

      <td>
        {feature.name ||
          definition?.name ||
          "Unknown feature"}
      </td>

      <td>
        <span className="feature-value">
          {formatFeatureValue(
            feature.value,
            dataType,
          )}
        </span>
      </td>

      <td>
        <span className="feature-data-type">
          {dataType || "—"}
        </span>
      </td>
    </tr>
  );
}

// ============================================================
// FEATURE CALCULATION CARD
// ============================================================

function FeatureCalculation({ feature }) {
  const definition = getFeatureDefinition(feature.id);

  const dataType =
    feature.dataType ||
    definition?.dataType;

  return (
    <article className="feature-calculation-card">
      <div className="feature-calculation-card__header">
        <div>
          <span className="feature-calculation-card__id">
            {feature.id}
          </span>

          <h3>
            {feature.name ||
              definition?.name ||
              "Unknown feature"}
          </h3>
        </div>

        <span className="feature-calculation-card__value">
          {formatFeatureValue(
            feature.value,
            dataType,
          )}
        </span>
      </div>

      <div className="feature-calculation-card__body">
        <div className="feature-calculation-field">
          <span>Description</span>

          <strong>
            {feature.description ||
              definition?.description ||
              "—"}
          </strong>
        </div>

        <div className="feature-calculation-field">
          <span>Source</span>

          <strong>
            {feature.source ||
              definition?.source ||
              "—"}
          </strong>
        </div>

        <div className="feature-calculation-field">
          <span>Calculation</span>

          <strong>
            {feature.calculation ||
              definition?.calculation ||
              "—"}
          </strong>
        </div>

        <div className="feature-calculation-field">
          <span>Raw Value</span>

          <strong>
            {formatFeatureValue(
              feature.rawValue ?? feature.value,
              dataType,
            )}
          </strong>
        </div>

        <div className="feature-calculation-field">
          <span>Data Type</span>

          <strong>
            {dataType || "—"}
          </strong>
        </div>

        <div className="feature-calculation-field">
          <span>Status</span>

          <StatusBadge
            status={
              feature.status ||
              FEATURE_STATUS.EXTRACTED
            }
          />
        </div>
      </div>
    </article>
  );
}

// ============================================================
// MAIN PAGE
// ============================================================

export default function FeatureDetails() {
  const emailId = useMemo(
    () => getEmailIdFromLocation(),
    [],
  );

  const [feature, setFeature] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [operationMessage, setOperationMessage] =
    useState(null);

  // ==========================================================
  // LOAD FEATURE
  // ==========================================================

  const loadFeature = useCallback(
    async ({ signal } = {}) => {
      if (!emailId) {
        setError(
          "No email ID was provided.",
        );

        setLoading(false);

        return;
      }

      setLoading(true);
      setError(null);

      try {
        const result =
          await featureService.getFeature(
            emailId,
            { signal },
          );

        setFeature(result);
      } catch (err) {
        if (err?.name === "AbortError") {
          return;
        }

        setError(
          err instanceof FeatureApiError
            ? err.message
            : "An unexpected error occurred while loading feature details.",
        );
      } finally {
        setLoading(false);
      }
    },
    [emailId],
  );

  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {
    const controller =
      new AbortController();

    loadFeature({
      signal: controller.signal,
    });

    return () => {
      controller.abort();
    };
  }, [loadFeature]);

  // ==========================================================
  // EXTRACT
  // ==========================================================

  const handleExtract = useCallback(
    async () => {
      if (!emailId) {
        return;
      }

      setExtracting(true);
      setError(null);
      setOperationMessage(null);

      try {
        const result =
          await featureService.extractFeatures(
            emailId,
          );

        setFeature(result);

        setOperationMessage(
          "Features extracted successfully.",
        );
      } catch (err) {
        setError(
          err instanceof FeatureApiError
            ? err.message
            : "Feature extraction failed.",
        );
      } finally {
        setExtracting(false);
      }
    },
    [emailId],
  );

  // ==========================================================
  // RE-EXTRACT
  // ==========================================================

  const handleReExtract =
    useCallback(
      async () => {
        if (!emailId) {
          return;
        }

        setExtracting(true);
        setError(null);
        setOperationMessage(null);

        try {
          const result =
            await featureService.reextractFeatures(
              emailId,
            );

          setFeature(result);

          setOperationMessage(
            "Features re-extracted successfully.",
          );
        } catch (err) {
          setError(
            err instanceof FeatureApiError
              ? err.message
              : "Feature re-extraction failed.",
          );
        } finally {
          setExtracting(false);
        }
      },
      [emailId],
    );

  // ==========================================================
  // BACK
  // ==========================================================

  const handleBack = useCallback(() => {
    window.location.href = "/features";
  }, []);

  // ==========================================================
  // DERIVED DATA
  // ==========================================================

  const featureVector =
    feature?.featureVector || {};

  const featureValues =
    feature?.featureValues || [];

  const normalizedFeatureValues =
    useMemo(() => {
      if (featureValues.length > 0) {
        return featureValues;
      }

      return FEATURE_DEFINITIONS.map(
        (definition) => ({
          id: definition.id,
          name: definition.name,
          description:
            definition.description,
          source: definition.source,
          calculation:
            definition.calculation,
          dataType:
            definition.dataType,
          value:
            featureVector[
              definition.id
            ],
        }),
      );
    }, [
      featureValues,
      featureVector,
    ]);

  const extractedCount =
    normalizedFeatureValues.filter(
      (item) =>
        item.value !== null &&
        item.value !== undefined,
    ).length;

  const featureStatus =
    feature?.status ||
    FEATURE_STATUS.PENDING;

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <main className="feature-details">
      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="feature-details__header">
        <div>
          <button
            type="button"
            className="feature-button feature-button--link feature-details__back"
            onClick={handleBack}
          >
            ← Back
          </button>

          <h1 className="feature-details__title">
            Feature Details
          </h1>

          <p className="feature-details__subtitle">
            Individual email feature vector and
            calculation details.
          </p>
        </div>

        <div className="feature-details__actions">
          {featureStatus ===
            FEATURE_STATUS.EXTRACTED ||
          featureStatus ===
            FEATURE_STATUS.WARNING ? (
            <button
              type="button"
              className="feature-button feature-button--primary"
              onClick={handleReExtract}
              disabled={
                loading ||
                extracting
              }
            >
              {extracting
                ? "Processing…"
                : "Re-extract Features"}
            </button>
          ) : (
            <button
              type="button"
              className="feature-button feature-button--primary"
              onClick={handleExtract}
              disabled={
                loading ||
                extracting
              }
            >
              {extracting
                ? "Extracting…"
                : "Extract Features"}
            </button>
          )}

          <button
            type="button"
            className="feature-button feature-button--secondary"
            onClick={() =>
              loadFeature()
            }
            disabled={
              loading ||
              extracting
            }
          >
            Refresh
          </button>
        </div>
      </header>

      {/* =====================================================
          OPERATION MESSAGE
      ===================================================== */}

      {operationMessage && (
        <div
          className="feature-details__notice"
          role="status"
        >
          {operationMessage}
        </div>
      )}

      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <ErrorState
          message={error}
          onRetry={() =>
            loadFeature()
          }
        />
      )}

      {/* =====================================================
          LOADING
      ===================================================== */}

      {loading ? (
        <LoadingState />
      ) : feature ? (
        <>
          {/* =================================================
              EMAIL INFORMATION
          ================================================= */}

          <section className="feature-details__section">
            <div className="feature-section-heading">
              <div>
                <h2>
                  Email Information
                </h2>

                <p>
                  Source email metadata used by the
                  Feature Engineering module.
                </p>
              </div>

              <StatusBadge
                status={featureStatus}
              />
            </div>

            <div className="feature-information-grid">
              <InformationItem
                label="Email ID"
                value={feature.emailId}
              />

              <InformationItem
                label="Sender"
                value={
                  feature.identity?.sender
                }
              />

              <InformationItem
                label="Subject"
                value={
                  feature.identity?.subject
                }
              />

              <InformationItem
                label="Message-ID"
                value={
                  feature.identity?.messageId
                }
              />

              <InformationItem
                label="Received"
                value={formatDateTime(
                  feature.timestamps
                    ?.receivedAt,
                )}
              />

              <InformationItem
                label="Parsed"
                value={formatDateTime(
                  feature.timestamps
                    ?.parsedAt,
                )}
              />
            </div>
          </section>

          {/* =================================================
              EXTRACTION METADATA
          ================================================= */}

          <section className="feature-details__section">
            <div className="feature-section-heading">
              <div>
                <h2>
                  Extraction Metadata
                </h2>

                <p>
                  Processing information for this feature
                  vector.
                </p>
              </div>
            </div>

            <div className="feature-information-grid">
              <InformationItem
                label="Feature Status"
                value={getFeatureStatusLabel(
                  featureStatus,
                )}
              />

              <InformationItem
                label="Features"
                value={`${extractedCount}/${FEATURE_COUNT}`}
              />

              <InformationItem
                label="Extractor Version"
                value={
                  feature.metadata
                    ?.extractorVersion
                }
              />

              <InformationItem
                label="Processing Time"
                value={
                  feature.metadata
                    ?.processingTimeMs !==
                  undefined
                    ? `${feature.metadata.processingTimeMs} ms`
                    : "—"
                }
              />

              <InformationItem
                label="Extracted At"
                value={formatDateTime(
                  feature.metadata
                    ?.extractedAt,
                )}
              />

              <InformationItem
                label="Feature Record ID"
                value={
                  feature.featureId
                }
              />
            </div>
          </section>

          {/* =================================================
              VALIDATION
          ================================================= */}

          {(feature.validation?.errors?.length ||
            feature.validation?.warnings?.length) ? (
            <section className="feature-details__section">
              <div className="feature-section-heading">
                <div>
                  <h2>
                    Validation
                  </h2>

                  <p>
                    Validation messages generated during
                    feature extraction.
                  </p>
                </div>
              </div>

              {feature.validation?.errors
                ?.length > 0 && (
                <div className="feature-validation feature-validation--error">
                  <strong>
                    Errors
                  </strong>

                  <ul>
                    {feature.validation.errors.map(
                      (message, index) => (
                        <li
                          key={`error-${index}`}
                        >
                          {message}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              )}

              {feature.validation?.warnings
                ?.length > 0 && (
                <div className="feature-validation feature-validation--warning">
                  <strong>
                    Warnings
                  </strong>

                  <ul>
                    {feature.validation.warnings.map(
                      (message, index) => (
                        <li
                          key={`warning-${index}`}
                        >
                          {message}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              )}
            </section>
          ) : null}

          {/* =================================================
              FEATURE VECTOR
          ================================================= */}

          <section className="feature-details__section">
            <div className="feature-section-heading">
              <div>
                <h2>
                  Feature Vector
                </h2>

                <p>
                  F1-F12 values extracted from this email.
                </p>
              </div>

              <span className="feature-vector-count">
                {extractedCount}/{FEATURE_COUNT}
              </span>
            </div>

            <div className="feature-table-wrapper">
              <table className="feature-table feature-vector-table">
                <thead>
                  <tr>
                    <th scope="col">
                      ID
                    </th>

                    <th scope="col">
                      Feature Name
                    </th>

                    <th scope="col">
                      Value
                    </th>

                    <th scope="col">
                      Type
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {normalizedFeatureValues.map(
                    (item) => (
                      <FeatureValueRow
                        key={item.id}
                        feature={item}
                      />
                    ),
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* =================================================
              FEATURE CALCULATION
          ================================================= */}

          <section className="feature-details__section">
            <div className="feature-section-heading">
              <div>
                <h2>
                  Feature Calculation
                </h2>

                <p>
                  Definition and calculation context for
                  every extracted feature.
                </p>
              </div>
            </div>

            <div className="feature-calculation-list">
              {normalizedFeatureValues.map(
                (item) => (
                  <FeatureCalculation
                    key={item.id}
                    feature={item}
                  />
                ),
              )}
            </div>
          </section>
        </>
      ) : (
        <div className="feature-details__state">
          No feature details are available.
        </div>
      )}
    </main>
  );
}
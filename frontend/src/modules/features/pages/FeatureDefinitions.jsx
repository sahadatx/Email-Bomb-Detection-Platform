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
  getFeatureDefinition,
} from "../types";


// ============================================================
// HELPERS
// ============================================================

function formatDataType(value) {
  if (!value) {
    return "—";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function formatSource(value) {
  if (!value) {
    return "—";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function getFeatureNumber(id) {
  const match = String(id ?? "").match(
    /^F(\d+)$/i,
  );

  if (!match) {
    return Number.MAX_SAFE_INTEGER;
  }

  return Number(match[1]);
}


function normalizeDefinition(definition) {
  if (!definition?.id) {
    return null;
  }

  const localDefinition =
    getFeatureDefinition(
      definition.id,
    );

  return {
    id: definition.id,

    name:
      definition.name ||
      localDefinition?.name ||
      "Unknown feature",

    description:
      definition.description ||
      localDefinition?.description ||
      "—",

    dataType:
      definition.dataType ||
      localDefinition?.dataType ||
      null,

    source:
      definition.source ||
      localDefinition?.source ||
      null,

    calculation:
      definition.calculation ||
      localDefinition?.calculation ||
      "—",
  };
}


function normalizeDefinitions(definitions) {
  if (!Array.isArray(definitions)) {
    return [];
  }

  return definitions
    .map(normalizeDefinition)
    .filter(Boolean)
    .sort(
      (left, right) =>
        getFeatureNumber(left.id) -
        getFeatureNumber(right.id),
    );
}


// ============================================================
// LOADING STATE
// ============================================================

function LoadingState() {
  return (
    <div
      className="feature-definitions__state"
      role="status"
      aria-live="polite"
    >
      <div className="feature-definitions__state-title">
        Loading feature definitions…
      </div>

      <div className="feature-definitions__state-message">
        Retrieving the authoritative F1–F12
        specification.
      </div>
    </div>
  );
}


// ============================================================
// ERROR STATE
// ============================================================

function ErrorState({
  message,
  onRetry,
}) {
  return (
    <div
      className="feature-definitions__state feature-definitions__state--error"
      role="alert"
    >
      <div className="feature-definitions__state-title">
        Unable to load feature definitions
      </div>

      <div className="feature-definitions__state-message">
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
// DEFINITION CARD
// ============================================================

function DefinitionCard({
  definition,
}) {
  return (
    <article className="feature-definition-card">
      <div className="feature-definition-card__header">
        <div className="feature-definition-card__identity">
          <span className="feature-definition-card__id">
            {definition.id}
          </span>

          <h3>
            {definition.name}
          </h3>
        </div>

        <span className="feature-definition-card__type">
          {formatDataType(
            definition.dataType,
          )}
        </span>
      </div>

      <div className="feature-definition-card__body">
        <div className="feature-definition-card__field">
          <span className="feature-definition-card__label">
            Description
          </span>

          <p>
            {definition.description}
          </p>
        </div>

        <div className="feature-definition-card__field">
          <span className="feature-definition-card__label">
            Source
          </span>

          <p>
            {formatSource(
              definition.source,
            )}
          </p>
        </div>

        <div className="feature-definition-card__field">
          <span className="feature-definition-card__label">
            Calculation
          </span>

          <p>
            {definition.calculation}
          </p>
        </div>
      </div>
    </article>
  );
}


// ============================================================
// DEFINITION TABLE
// ============================================================

function DefinitionTable({
  definitions,
}) {
  return (
    <div className="feature-table-wrapper">
      <table className="feature-table feature-definition-table">
        <thead>
          <tr>
            <th scope="col">
              ID
            </th>

            <th scope="col">
              Feature
            </th>

            <th scope="col">
              Description
            </th>

            <th scope="col">
              Type
            </th>

            <th scope="col">
              Source
            </th>

            <th scope="col">
              Calculation
            </th>
          </tr>
        </thead>

        <tbody>
          {definitions.map(
            (definition) => (
              <tr
                key={definition.id}
              >
                <td>
                  <strong className="feature-definition-id">
                    {definition.id}
                  </strong>
                </td>

                <td>
                  <strong>
                    {definition.name}
                  </strong>
                </td>

                <td>
                  <span className="feature-definition-description">
                    {definition.description}
                  </span>
                </td>

                <td>
                  <span className="feature-data-type">
                    {formatDataType(
                      definition.dataType,
                    )}
                  </span>
                </td>

                <td>
                  <span className="feature-definition-source">
                    {formatSource(
                      definition.source,
                    )}
                  </span>
                </td>

                <td>
                  <span className="feature-definition-calculation">
                    {definition.calculation}
                  </span>
                </td>
              </tr>
            ),
          )}
        </tbody>
      </table>
    </div>
  );
}


// ============================================================
// MAIN PAGE
// ============================================================

export default function FeatureDefinitions() {
  const [
    definitions,
    setDefinitions,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(null);

  // ==========================================================
  // LOAD DEFINITIONS
  // ==========================================================

  const loadDefinitions =
    useCallback(
      async ({
        signal,
      } = {}) => {
        setLoading(true);
        setError(null);

        try {
          const result =
            await featureService.getFeatureDefinitions({
              signal,
            });

          const backendDefinitions =
            Array.isArray(result)
              ? result
              : result?.items || [];

          setDefinitions(
            backendDefinitions,
          );
        } catch (err) {
          if (
            err?.name ===
            "AbortError"
          ) {
            return;
          }

          setError(
            err instanceof FeatureApiError
              ? err.message
              : "An unexpected error occurred while loading feature definitions.",
          );
        } finally {
          setLoading(false);
        }
      },
      [],
    );

  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {
    const controller =
      new AbortController();

    loadDefinitions({
      signal:
        controller.signal,
    });

    return () => {
      controller.abort();
    };
  }, [loadDefinitions]);

  // ==========================================================
  // DISPLAY DEFINITIONS
  // ==========================================================

  const displayDefinitions =
    useMemo(() => {
      const normalizedBackend =
        normalizeDefinitions(
          definitions,
        );

      if (
        normalizedBackend.length > 0
      ) {
        return normalizedBackend;
      }

      return normalizeDefinitions(
        FEATURE_DEFINITIONS,
      );
    }, [definitions]);

  // ==========================================================
  // DEFINITION COUNT
  // ==========================================================

  const definitionCount =
    displayDefinitions.length;

  const completeSpecification =
    definitionCount ===
    FEATURE_COUNT;

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <main className="feature-definitions">
      {/* ================================================== */}
      {/* HEADER                                             */}
      {/* ================================================== */}

      <header className="feature-definitions__header">
        <div>
          <button
            type="button"
            className="feature-button feature-button--link feature-definitions__back"
            onClick={() => {
              window.location.href =
                "/features";
            }}
          >
            ← Back
          </button>

          <h1 className="feature-definitions__title">
            Feature Definitions
          </h1>

          <p className="feature-definitions__subtitle">
            F1–F12 Feature Engineering
            specification, including data types,
            sources, and calculation rules.
          </p>
        </div>

        <button
          type="button"
          className="feature-button feature-button--secondary"
          onClick={() =>
            loadDefinitions()
          }
          disabled={loading}
        >
          {loading
            ? "Refreshing…"
            : "Refresh"}
        </button>
      </header>

      {/* ================================================== */}
      {/* OVERVIEW                                           */}
      {/* ================================================== */}

      <section
        className="feature-definitions__overview"
        aria-label="Feature definition overview"
      >
        <div className="feature-definition-overview-card">
          <span className="feature-definition-overview-card__label">
            Total Features
          </span>

          <strong className="feature-definition-overview-card__value">
            {FEATURE_COUNT}
          </strong>
        </div>

        <div className="feature-definition-overview-card">
          <span className="feature-definition-overview-card__label">
            Specification
          </span>

          <strong className="feature-definition-overview-card__value">
            F1–F12
          </strong>
        </div>

        <div className="feature-definition-overview-card">
          <span className="feature-definition-overview-card__label">
            Source
          </span>

          <strong className="feature-definition-overview-card__value">
            Parsed Email
          </strong>
        </div>
      </section>

      {/* ================================================== */}
      {/* ERROR                                             */}
      {/* ================================================== */}

      {error && (
        <ErrorState
          message={error}
          onRetry={() =>
            loadDefinitions()
          }
        />
      )}

      {/* ================================================== */}
      {/* DEFINITION TABLE                                  */}
      {/* ================================================== */}

      <section className="feature-definitions__section">
        <div className="feature-section-heading">
          <div>
            <h2>
              F1–F12 Definitions
            </h2>

            <p>
              Authoritative feature definitions
              used by the Feature Engineering
              module.
            </p>
          </div>

          <span className="feature-definitions__count">
            {definitionCount} /{" "}
            {FEATURE_COUNT}
          </span>
        </div>

        {loading ? (
          <LoadingState />
        ) : definitionCount === 0 ? (
          <div className="feature-definitions__state">
            <div className="feature-definitions__state-title">
              No feature definitions available
            </div>

            <div className="feature-definitions__state-message">
              The Feature Engineering
              specification could not be loaded.
            </div>

            <button
              type="button"
              className="feature-button feature-button--secondary"
              onClick={() =>
                loadDefinitions()
              }
            >
              Retry
            </button>
          </div>
        ) : (
          <DefinitionTable
            definitions={
              displayDefinitions
            }
          />
        )}
      </section>

      {/* ================================================== */}
      {/* DETAIL CARDS                                      */}
      {/* ================================================== */}

      {!loading &&
        displayDefinitions.length > 0 && (
          <section className="feature-definitions__section">
            <div className="feature-section-heading">
              <div>
                <h2>
                  Feature Reference
                </h2>

                <p>
                  Detailed reference for each
                  F1–F12 feature.
                </p>
              </div>

              <span className="feature-definitions__count">
                {completeSpecification
                  ? "Complete"
                  : `${definitionCount} / ${FEATURE_COUNT}`}
              </span>
            </div>

            <div className="feature-definition-card-grid">
              {displayDefinitions.map(
                (definition) => (
                  <DefinitionCard
                    key={
                      definition.id
                    }
                    definition={
                      definition
                    }
                  />
                ),
              )}
            </div>
          </section>
        )}
    </main>
  );
}

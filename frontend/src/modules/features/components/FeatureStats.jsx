import React from "react";

import { FEATURE_COUNT } from "../types";

// ============================================================
// SUMMARY CARD
// ============================================================

function SummaryCard({
  label,
  value,
  description,
  loading = false,
  variant = "default",
}) {
  return (
    <article
      className={`feature-stats__card feature-stats__card--${variant}`}
    >
      <div className="feature-stats__card-label">
        {label}
      </div>

      <div className="feature-stats__card-value">
        {loading ? "…" : value}
      </div>

      {description && (
        <div className="feature-stats__card-description">
          {description}
        </div>
      )}
    </article>
  );
}

// ============================================================
// VALUE NORMALIZER
// ============================================================

function normalizeNumber(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, number);
}

// ============================================================
// MAIN COMPONENT
// ============================================================

export default function FeatureStats({
  summary = {},
  loading = false,
}) {
  // ----------------------------------------------------------
  // Normalize summary values.
  // ----------------------------------------------------------

  const totalCollected = normalizeNumber(
    summary.totalCollected,
  );

  const totalParsed = normalizeNumber(
    summary.totalParsed,
  );

  const totalFeaturesReady = normalizeNumber(
    summary.totalFeaturesReady,
  );

  const totalPending = normalizeNumber(
    summary.totalPending,
  );

  const totalFailed = normalizeNumber(
    summary.totalFailed,
  );

  // ----------------------------------------------------------
  // Calculate parsed percentage.
  //
  // Denominator:
  // Collected emails
  // ----------------------------------------------------------

  const parsedPercentage =
    totalCollected > 0
      ? Math.round(
          (totalParsed / totalCollected) * 100,
        )
      : 0;

  // ----------------------------------------------------------
  // Calculate feature readiness percentage.
  //
  // Denominator:
  // Parsed emails
  // ----------------------------------------------------------

  const featureReadyPercentage =
    totalParsed > 0
      ? Math.round(
          (totalFeaturesReady / totalParsed) * 100,
        )
      : 0;

  return (
    <section
      className="feature-stats"
      aria-labelledby="feature-stats-title"
    >
      {/* ==================================================== */}
      {/* SECTION HEADING                                      */}
      {/* ==================================================== */}

      <div className="feature-section-heading">
        <div>
          <h2 id="feature-stats-title">
            Feature Engineering Summary
          </h2>

          <p>
            Current Feature Engineering processing status.
          </p>
        </div>
      </div>

      {/* ==================================================== */}
      {/* SUMMARY GRID                                         */}
      {/* ==================================================== */}

      <div className="feature-stats__grid">
        {/* ================================================== */}
        {/* PARSED                                             */}
        {/* ================================================== */}

        <SummaryCard
          label="Parsed Emails"
          value={totalParsed}
          description={
            totalCollected > 0
              ? `${parsedPercentage}% of ${totalCollected} collected`
              : "No collected emails"
          }
          loading={loading}
          variant="parsed"
        />

        {/* ================================================== */}
        {/* FEATURES READY                                     */}
        {/* ================================================== */}

        <SummaryCard
          label="Features Ready"
          value={totalFeaturesReady}
          description={
            totalParsed > 0
              ? `${featureReadyPercentage}% of parsed emails`
              : `${FEATURE_COUNT} features per email`
          }
          loading={loading}
          variant="ready"
        />

        {/* ================================================== */}
        {/* PENDING                                             */}
        {/* ================================================== */}

        <SummaryCard
          label="Pending"
          value={totalPending}
          description="Awaiting feature extraction"
          loading={loading}
          variant="pending"
        />

        {/* ================================================== */}
        {/* FAILED                                              */}
        {/* ================================================== */}

        <SummaryCard
          label="Failed"
          value={totalFailed}
          description={
            totalFailed > 0
              ? "Feature extraction failed"
              : "No failed extractions"
          }
          loading={loading}
          variant="failed"
        />
      </div>
    </section>
  );
}
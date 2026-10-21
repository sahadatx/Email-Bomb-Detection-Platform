import React from "react";


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function FeatureReadiness({
  percentage = 0,
  ready = 0,
  total = 0,
  pending = 0,
  failed = 0,
  loading = false,
}) {
  const normalizedPercentage = Math.min(
    100,
    Math.max(
      0,
      Number(percentage) || 0,
    ),
  );

  return (
    <section
      className="feature-readiness"
      aria-labelledby="feature-readiness-title"
    >
      <div className="feature-readiness__header">
        <div>
          <h2 id="feature-readiness-title">
            Feature Readiness
          </h2>

          <p>
            Progress of email feature extraction.
          </p>
        </div>

        <strong className="feature-readiness__percentage">
          {loading
            ? "…"
            : `${normalizedPercentage}%`}
        </strong>
      </div>

      <div
        className="feature-readiness__track"
        role="progressbar"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={
          normalizedPercentage
        }
        aria-label="Feature extraction readiness"
      >
        <div
          className="feature-readiness__value"
          style={{
            width: `${normalizedPercentage}%`,
          }}
        />
      </div>

      <div className="feature-readiness__meta">
        <span>
          {loading
            ? "Loading…"
            : `${ready} / ${total} emails with extracted features`}
        </span>

        <span>
          {loading
            ? "—"
            : `${pending} pending`}
        </span>

        <span>
          {loading
            ? "—"
            : `${failed} failed`}
        </span>
      </div>
    </section>
  );
}
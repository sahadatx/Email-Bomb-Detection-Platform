import React from "react";
import { EVALUATION_METRIC_LABELS } from "../types";

const METRIC_KEYS = [
  "accuracy",
  "precision",
  "recall",
  "f1_score",
  "roc_auc",
];

function formatMetric(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "—";
  }

  return `${(numericValue * 100).toFixed(2)}%`;
}

export default function EvaluationMetrics({ evaluation }) {
  if (!evaluation) {
    return null;
  }

  return (
    <section className="ml-evaluation-metrics">
      <div className="ml-evaluation-section-heading">
        <div>
          <h3>Evaluation Metrics</h3>
          <p>Performance metrics for this evaluation run.</p>
        </div>
      </div>

      <div className="ml-evaluation-metric-grid">
        {METRIC_KEYS.map((key) => (
          <article className="ml-evaluation-metric-card" key={key}>
            <span className="ml-evaluation-metric-label">
              {EVALUATION_METRIC_LABELS[key] || key}
            </span>

            <strong className="ml-evaluation-metric-value">
              {formatMetric(evaluation[key])}
            </strong>
          </article>
        ))}
      </div>
    </section>
  );
}
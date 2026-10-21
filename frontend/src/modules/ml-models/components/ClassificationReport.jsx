import React from "react";

function formatScore(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "—";
  }

  return numericValue.toFixed(4);
}

function formatCount(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const numericValue = Number(value);

  return Number.isFinite(numericValue)
    ? numericValue.toLocaleString()
    : "—";
}

function normalizeReport(report) {
  if (!report || typeof report !== "object") {
    return [];
  }

  return Object.entries(report).filter(
    ([, value]) => value && typeof value === "object" && !Array.isArray(value)
  );
}

export default function ClassificationReport({ report }) {
  const entries = normalizeReport(report);

  if (entries.length === 0) {
    return (
      <section className="ml-evaluation-panel">
        <div className="ml-evaluation-section-heading">
          <div>
            <h3>Classification Report</h3>
            <p>Per-class precision, recall, F1-score, and support.</p>
          </div>
        </div>

        <div className="ml-evaluation-empty">
          Classification report is not available.
        </div>
      </section>
    );
  }

  return (
    <section className="ml-evaluation-panel">
      <div className="ml-evaluation-section-heading">
        <div>
          <h3>Classification Report</h3>
          <p>Per-class performance and aggregate scores.</p>
        </div>
      </div>

      <div className="ml-evaluation-table-wrapper">
        <table className="ml-evaluation-report-table">
          <thead>
            <tr>
              <th scope="col">Class</th>
              <th scope="col">Precision</th>
              <th scope="col">Recall</th>
              <th scope="col">F1-score</th>
              <th scope="col">Support</th>
            </tr>
          </thead>

          <tbody>
            {entries.map(([className, values]) => (
              <tr key={className}>
                <th scope="row">{className}</th>
                <td>{formatScore(values.precision)}</td>
                <td>{formatScore(values.recall)}</td>
                <td>{formatScore(values["f1-score"] ?? values.f1_score)}</td>
                <td>{formatCount(values.support)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
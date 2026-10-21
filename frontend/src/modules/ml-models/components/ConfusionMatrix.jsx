import React from "react";

function normalizeMatrix(matrix) {
  if (matrix && !Array.isArray(matrix) && typeof matrix === "object") {
    const keys = ["true_negative", "false_positive", "false_negative", "true_positive"];
    if (keys.every((key) => matrix[key] !== undefined)) {
      return [
        [matrix.true_negative, matrix.false_positive],
        [matrix.false_negative, matrix.true_positive],
      ];
    }
  }
  if (!Array.isArray(matrix)) {
    return [];
  }

  return matrix.map((row) => {
    if (Array.isArray(row)) {
      return row;
    }

    return [];
  });
}

export default function ConfusionMatrix({ matrix }) {
  const rows = normalizeMatrix(matrix);

  if (rows.length === 0) {
    return (
      <section className="ml-evaluation-panel">
        <div className="ml-evaluation-section-heading">
          <div>
            <h3>Confusion Matrix</h3>
            <p>Actual versus predicted class counts.</p>
          </div>
        </div>

        <div className="ml-evaluation-empty">
          Confusion matrix is not available.
        </div>
      </section>
    );
  }

  const columnCount = Math.max(0, ...rows.map((row) => row.length));
  const labels = columnCount === 2
    ? ["Normal", "Bomb"]
    : Array.from({ length: columnCount }, (_, index) => `Class ${index}`);

  return (
    <section className="ml-evaluation-panel">
      <div className="ml-evaluation-section-heading">
        <div>
          <h3>Confusion Matrix</h3>
          <p>Rows represent actual classes; columns represent predicted classes.</p>
        </div>
      </div>

      <div className="ml-evaluation-table-wrapper">
        <table className="ml-evaluation-confusion-table">
          <thead>
            <tr>
              <th scope="col">Actual / Predicted</th>
              {labels.map((label) => (
                <th scope="col" key={label}>
                  {label}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`row-${rowIndex}`}>
                <th scope="row">{labels[rowIndex] || `Class ${rowIndex}`}</th>

                {Array.from({ length: columnCount }, (_, columnIndex) => {
                  const value = row[columnIndex];
                  const numericValue = Number(value);
                  const valid = Number.isFinite(numericValue);

                  return (
                    <td
                      key={`cell-${rowIndex}-${columnIndex}`}
                      className={
                        rowIndex === columnIndex
                          ? "ml-confusion-cell-diagonal"
                          : ""
                      }
                    >
                      {value === null || value === undefined || !valid
                        ? "—"
                        : numericValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

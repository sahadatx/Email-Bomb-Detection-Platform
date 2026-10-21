import React from "react";


// ============================================================
// HELPERS
// ============================================================

function formatValue(
  value,
  dataType,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (
    dataType === "boolean"
  ) {
    return value
      ? "True"
      : "False";
  }

  if (
    dataType === "integer" ||
    dataType === "number"
  ) {
    return String(value);
  }

  return String(value);
}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function FeatureValue({
  id,
  name,
  value,
  dataType,
  status,
  compact = false,
}) {
  const displayValue =
    formatValue(
      value,
      dataType,
    );

  const valueClass = [
    "feature-value",
    compact
      ? "feature-value--compact"
      : "",
    dataType === "boolean"
      ? value
        ? "feature-value--true"
        : "feature-value--false"
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className="feature-value-wrapper"
      data-feature-id={id}
    >
      {!compact && (
        <div className="feature-value-wrapper__header">
          <div>
            <span className="feature-value-wrapper__id">
              {id}
            </span>

            {name && (
              <span className="feature-value-wrapper__name">
                {name}
              </span>
            )}
          </div>

          {status && (
            <span className="feature-value-wrapper__status">
              {status}
            </span>
          )}
        </div>
      )}

      <span
        className={valueClass}
        title={
          typeof value === "string"
            ? value
            : undefined
        }
      >
        {displayValue}
      </span>
    </div>
  );
}
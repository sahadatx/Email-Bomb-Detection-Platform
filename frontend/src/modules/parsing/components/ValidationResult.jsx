function normalizeMessages(items) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .filter(
      (item) =>
        item !== null &&
        item !== undefined &&
        String(item).trim() !== "",
    )
    .map((item) => String(item));
}

function ValidationList({
  title,
  items = [],
  variant,
}) {
  const messages =
    normalizeMessages(items);

  if (messages.length === 0) {
    return null;
  }

  return (
    <div
      className={`parsing-validation-list parsing-validation-list--${variant}`}
    >
      <header>
        <span>{title}</span>

        <strong>
          {messages.length}
        </strong>
      </header>

      <ul>
        {messages.map(
          (message, index) => (
            <li
              key={`${variant}-${message}-${index}`}
            >
              <span
                className="parsing-validation-list__icon"
                aria-hidden="true"
              >
                {variant === "error"
                  ? "!"
                  : "⚠"}
              </span>

              <span>
                {message}
              </span>
            </li>
          ),
        )}
      </ul>
    </div>
  );
}

export default function ValidationResult({
  validation = {},
}) {
  const errors =
    normalizeMessages(
      validation?.validation_errors ??
        validation?.errors,
    );

  const warnings =
    normalizeMessages(
      validation?.validation_warnings ??
        validation?.warnings,
    );

  const explicitValidity =
    validation?.is_valid;

  const isValid =
    explicitValidity !== false &&
    errors.length === 0;

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            VALIDATION
          </span>

          <h2>
            Validation &amp; Integrity
          </h2>

          <p>
            Structural validation and parsing
            integrity results.
          </p>
        </div>

        <span
          className={
            isValid
              ? "parsing-validation-badge parsing-validation-badge--valid"
              : "parsing-validation-badge parsing-validation-badge--invalid"
          }
          aria-label={
            isValid
              ? "Validation valid"
              : "Validation issues detected"
          }
        >
          {isValid
            ? "Valid"
            : "Issues Detected"}
        </span>
      </header>

      <div className="parsing-validation-summary">
        <div>
          <span>Errors</span>

          <strong>
            {errors.length}
          </strong>
        </div>

        <div>
          <span>Warnings</span>

          <strong>
            {warnings.length}
          </strong>
        </div>

        <div>
          <span>Integrity</span>

          <strong>
            {isValid
              ? "PASS"
              : "REVIEW"}
          </strong>
        </div>
      </div>

      <div className="parsing-validation-results">
        <ValidationList
          title="Errors"
          items={errors}
          variant="error"
        />

        <ValidationList
          title="Warnings"
          items={warnings}
          variant="warning"
        />

        {errors.length === 0 &&
          warnings.length === 0 && (
            <div className="parsing-validation-success">
              <strong>
                Validation completed successfully.
              </strong>

              <span>
                No structural errors or warnings
                were reported by the parser.
              </span>
            </div>
          )}
      </div>
    </section>
  );
}
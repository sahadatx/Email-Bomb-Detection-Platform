/**
 * Header Analysis
 *
 * Displays the complete normalized MIME
 * header collection.
 */

function formatHeaderValue(value) {
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return "—";
    }

    return value
      .map((item) => String(item))
      .join("\n");
  }

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return String(value);
}

function normalizeHeaders(headers) {
  if (
    !headers ||
    typeof headers !== "object" ||
    Array.isArray(headers)
  ) {
    return {};
  }

  return headers;
}

export default function HeaderAnalysis({
  headers = {},
}) {
  const normalizedHeaders =
    normalizeHeaders(headers);

  const entries = Object.entries(
    normalizedHeaders,
  );

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            MIME METADATA
          </span>

          <h2>Header Analysis</h2>

          <p>
            Normalized email headers extracted from
            the MIME message.
          </p>
        </div>

        <span className="parsing-detail-card__count">
          {entries.length} header
          {entries.length === 1
            ? ""
            : "s"}
        </span>
      </header>

      {entries.length === 0 ? (
        <div className="parsing-empty-state">
          <strong>
            No headers available.
          </strong>

          <span>
            The parser did not return any normalized
            header values.
          </span>
        </div>
      ) : (
        <div className="parsing-header-table-wrapper">
          <table className="parsing-header-table">
            <thead>
              <tr>
                <th scope="col">
                  Header
                </th>

                <th scope="col">
                  Value
                </th>
              </tr>
            </thead>

            <tbody>
              {entries.map(
                ([name, value]) => (
                  <tr key={name}>
                    <td>
                      <code>{name}</code>
                    </td>

                    <td>
                      <div className="parsing-header-value">
                        {formatHeaderValue(
                          value,
                        )}
                      </div>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
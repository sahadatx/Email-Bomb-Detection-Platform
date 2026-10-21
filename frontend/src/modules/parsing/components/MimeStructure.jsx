import { useMemo, useState } from "react";

/**
 * MIME Structure
 *
 * Displays the normalized MIME structure returned
 * by the Module 03 parsing pipeline.
 */

function formatSize(bytes) {
  if (
    bytes === null ||
    bytes === undefined ||
    bytes === ""
  ) {
    return "—";
  }

  const size = Number(bytes);

  if (!Number.isFinite(size) || size < 0) {
    return "—";
  }

  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  if (size < 1024 * 1024 * 1024) {
    return `${(
      size /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  }

  return `${(
    size /
    (1024 * 1024 * 1024)
  ).toFixed(1)} GB`;
}

function getStringValue(
  value,
  fallback = "—",
) {
  if (
    value === null ||
    value === undefined ||
    String(value).trim() === ""
  ) {
    return fallback;
  }

  return String(value);
}

function MimePart({
  part = {},
  index,
  depth = 0,
}) {
  const [expanded, setExpanded] =
    useState(false);

  const contentType =
    getStringValue(
      part?.content_type,
      "unknown",
    );

  const disposition =
    getStringValue(
      part?.content_disposition,
      "inline",
    );

  const charset =
    getStringValue(part?.charset);

  const filename =
    getStringValue(part?.filename);

  const contentId =
    getStringValue(part?.content_id);

  const size = formatSize(part?.size);

  const hasDetails =
    Boolean(
      part?.charset ||
        part?.filename ||
        part?.content_disposition ||
        part?.content_id ||
        part?.size !== null &&
          part?.size !== undefined,
    );

  function toggleExpanded() {
    if (!hasDetails) {
      return;
    }

    setExpanded(
      (current) => !current,
    );
  }

  return (
    <div
      className="parsing-mime-node"
      style={{
        "--mime-depth": depth,
      }}
    >
      <button
        type="button"
        className="parsing-mime-node__header"
        onClick={toggleExpanded}
        disabled={!hasDetails}
        aria-expanded={
          hasDetails
            ? expanded
            : undefined
        }
        aria-label={
          hasDetails
            ? `${expanded ? "Collapse" : "Expand"} MIME part ${index}`
            : `MIME part ${index}`
        }
      >
        <span
          className="parsing-mime-node__icon"
          aria-hidden="true"
        >
          {hasDetails
            ? expanded
              ? "−"
              : "+"
            : "•"}
        </span>

        <span className="parsing-mime-node__index">
          Part {index}
        </span>

        <strong title={contentType}>
          {contentType}
        </strong>

        <span className="parsing-mime-node__size">
          {size}
        </span>
      </button>

      {expanded && (
        <div className="parsing-mime-node__details">
          <div>
            <span>
              Content Type
            </span>

            <strong>
              {contentType}
            </strong>
          </div>

          <div>
            <span>
              Disposition
            </span>

            <strong>
              {disposition}
            </strong>
          </div>

          <div>
            <span>
              Charset
            </span>

            <strong>
              {charset}
            </strong>
          </div>

          <div>
            <span>
              Filename
            </span>

            <strong>
              {filename}
            </strong>
          </div>

          <div>
            <span>
              Size
            </span>

            <strong>
              {size}
            </strong>
          </div>

          <div>
            <span>
              Content ID
            </span>

            <strong>
              {contentId}
            </strong>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MimeStructure({
  mimeParts = [],
}) {
  const parts = useMemo(
    () =>
      Array.isArray(mimeParts)
        ? mimeParts
        : [],
    [mimeParts],
  );

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            MIME STRUCTURE
          </span>

          <h2>MIME Structure</h2>

          <p>
            Parsed MIME parts and their
            structural metadata.
          </p>
        </div>

        <span className="parsing-detail-card__count">
          {parts.length} part
          {parts.length === 1
            ? ""
            : "s"}
        </span>
      </header>

      {parts.length === 0 ? (
        <div className="parsing-empty-state">
          <strong>
            No MIME parts available.
          </strong>

          <span>
            The parser did not return any MIME
            structure information.
          </span>
        </div>
      ) : (
        <div className="parsing-mime-tree">
          {parts.map((part, index) => (
            <MimePart
              key={
                part?.part_id ||
                part?.content_id ||
                `${part?.content_type || "part"}-${index}`
              }
              part={part}
              index={index + 1}
              depth={0}
            />
          ))}
        </div>
      )}
    </section>
  );
}
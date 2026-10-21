import { useMemo, useState } from "react";

/**
 * Content Inspector
 *
 * Allows analysts to inspect normalized text
 * and HTML message bodies.
 *
 * HTML is intentionally rendered as source text
 * rather than injected into the DOM.
 */

const CONTENT_TAB = Object.freeze({
  TEXT: "text",
  HTML: "html",
});

function getContent(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "";
  }

  return String(value);
}

function getTabLabel(activeTab) {
  switch (activeTab) {
    case CONTENT_TAB.HTML:
      return "HTML body source";

    case CONTENT_TAB.TEXT:
    default:
      return "Normalized plain-text body";
  }
}

export default function ContentInspector({
  textBody = null,
  htmlBody = null,
}) {
  const [
    activeTab,
    setActiveTab,
  ] = useState(CONTENT_TAB.TEXT);

  const content = useMemo(() => {
    switch (activeTab) {
      case CONTENT_TAB.HTML:
        return getContent(htmlBody);

      case CONTENT_TAB.TEXT:
      default:
        return getContent(textBody);
    }
  }, [
    activeTab,
    textBody,
    htmlBody,
  ]);

  const isEmpty = content.length === 0;

  const textAvailable =
    getContent(textBody).length > 0;

  const htmlAvailable =
    getContent(htmlBody).length > 0;

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            CONTENT
          </span>

          <h2>Content Inspector</h2>

          <p>
            Inspect normalized message content
            extracted from the MIME message.
          </p>
        </div>
      </header>

      <div
        className="parsing-content-tabs"
        role="tablist"
        aria-label="Email content representations"
      >
        <button
          type="button"
          role="tab"
          aria-selected={
            activeTab === CONTENT_TAB.TEXT
          }
          aria-controls="parsing-content-panel"
          className={
            activeTab === CONTENT_TAB.TEXT
              ? "parsing-content-tab parsing-content-tab--active"
              : "parsing-content-tab"
          }
          onClick={() =>
            setActiveTab(CONTENT_TAB.TEXT)
          }
        >
          TEXT
          {!textAvailable && " — EMPTY"}
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={
            activeTab === CONTENT_TAB.HTML
          }
          aria-controls="parsing-content-panel"
          className={
            activeTab === CONTENT_TAB.HTML
              ? "parsing-content-tab parsing-content-tab--active"
              : "parsing-content-tab"
          }
          onClick={() =>
            setActiveTab(CONTENT_TAB.HTML)
          }
        >
          HTML
          {!htmlAvailable && " — EMPTY"}
        </button>
      </div>

      <div
        id="parsing-content-panel"
        className="parsing-content-panel"
        role="tabpanel"
      >
        <div className="parsing-content-panel__toolbar">
          <span>
            {getTabLabel(activeTab)}
          </span>

          <span>
            {content.length} characters
          </span>
        </div>

        {isEmpty ? (
          <div className="parsing-empty-state">
            <strong>
              No content available.
            </strong>

            <span>
              This message does not contain content
              for the selected representation.
            </span>
          </div>
        ) : (
          <pre className="parsing-content-viewer">
            <code>{content}</code>
          </pre>
        )}
      </div>
    </section>
  );
}
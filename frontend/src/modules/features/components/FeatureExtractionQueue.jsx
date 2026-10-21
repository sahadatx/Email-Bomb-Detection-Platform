import React, { useMemo } from "react";


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function FeatureExtractionQueue({
  items = [],
  selectedEmailIds = new Set(),
  onToggleSelection,
  onSelectAll,
  onClearSelection,
  onExtract,
  extracting = false,
  loading = false,
}) {
  // ----------------------------------------------------------
  // Normalize selected IDs
  // ----------------------------------------------------------

  const selectedIds = useMemo(() => {
    if (
      selectedEmailIds instanceof Set
    ) {
      return selectedEmailIds;
    }

    if (
      Array.isArray(selectedEmailIds)
    ) {
      return new Set(
        selectedEmailIds,
      );
    }

    return new Set();
  }, [selectedEmailIds]);

  // ----------------------------------------------------------
  // Only parsed emails can enter extraction queue.
  // ----------------------------------------------------------

  const selectableItems =
    useMemo(
      () =>
        items.filter(
          (item) =>
            item.parsed === true,
        ),
      [items],
    );

  // ----------------------------------------------------------
  // Selected items
  // ----------------------------------------------------------

  const selectedItems =
    useMemo(
      () =>
        selectableItems.filter(
          (item) =>
            selectedIds.has(
              item.emailId,
            ),
        ),
      [
        selectableItems,
        selectedIds,
      ],
    );

  const allSelected =
    selectableItems.length > 0 &&
    selectableItems.every(
      (item) =>
        selectedIds.has(
          item.emailId,
        ),
    );

  // ----------------------------------------------------------
  // Action state
  // ----------------------------------------------------------

  const controlsDisabled =
    loading ||
    extracting;

  const extractDisabled =
    controlsDisabled ||
    selectedIds.size === 0;

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <section
      className="feature-extraction-queue"
      aria-labelledby="feature-extraction-queue-title"
    >
      {/* ==================================================== */}
      {/* HEADER                                               */}
      {/* ==================================================== */}

      <div className="feature-extraction-queue__header">
        <div>
          <h2
            id="feature-extraction-queue-title"
          >
            Feature Extraction
          </h2>

          <p>
            Select parsed emails and extract their
            F1-F12 feature vectors.
          </p>
        </div>

        <div className="feature-extraction-queue__count">
          <strong>
            {selectedIds.size}
          </strong>

          <span>
            selected
          </span>
        </div>
      </div>

      {/* ==================================================== */}
      {/* CONTROLS                                             */}
      {/* ==================================================== */}

      <div className="feature-extraction-queue__controls">
        <button
          type="button"
          className="feature-button feature-button--secondary"
          onClick={
            allSelected
              ? onClearSelection
              : onSelectAll
          }
          disabled={
            controlsDisabled ||
            selectableItems.length === 0
          }
        >
          {allSelected
            ? "Clear All"
            : "Select All"}
        </button>

        <button
          type="button"
          className="feature-button feature-button--secondary"
          onClick={onClearSelection}
          disabled={
            controlsDisabled ||
            selectedIds.size === 0
          }
        >
          Clear
        </button>

        <button
          type="button"
          className="feature-button feature-button--primary"
          onClick={onExtract}
          disabled={
            extractDisabled
          }
        >
          {extracting
            ? "Extracting…"
            : `Extract Features${
                selectedIds.size > 0
                  ? ` (${selectedIds.size})`
                  : ""
              }`}
        </button>
      </div>

      {/* ==================================================== */}
      {/* QUEUE SUMMARY                                        */}
      {/* ==================================================== */}

      <div className="feature-extraction-queue__summary">
        <div className="feature-extraction-queue__summary-item">
          <span>
            Parsed
          </span>

          <strong>
            {selectableItems.length}
          </strong>
        </div>

        <div className="feature-extraction-queue__summary-item">
          <span>
            Selected
          </span>

          <strong>
            {selectedIds.size}
          </strong>
        </div>

        <div className="feature-extraction-queue__summary-item">
          <span>
            Queue
          </span>

          <strong>
            {selectedItems.length}
          </strong>
        </div>
      </div>

      {/* ==================================================== */}
      {/* SELECTED QUEUE                                      */}
      {/* ==================================================== */}

      {selectedItems.length > 0 && (
        <div className="feature-extraction-queue__list">
          <div className="feature-extraction-queue__list-header">
            <strong>
              Extraction Queue
            </strong>

            <span>
              {selectedItems.length} email
              {selectedItems.length === 1
                ? ""
                : "s"}
            </span>
          </div>

          <div className="feature-extraction-queue__items">
            {selectedItems.map(
              (item) => (
                <div
                  className="feature-extraction-queue__item"
                  key={
                    item.emailId
                  }
                >
                  <input
                    type="checkbox"
                    checked
                    disabled={
                      controlsDisabled
                    }
                    onChange={() =>
                      onToggleSelection?.(
                        item.emailId,
                      )
                    }
                    aria-label={`Remove ${
                      item.subject ||
                      item.emailId
                    } from extraction queue`}
                  />

                  <div className="feature-extraction-queue__item-content">
                    <div className="feature-extraction-queue__item-subject">
                      {item.subject ||
                        "No subject"}
                    </div>

                    <div className="feature-extraction-queue__item-sender">
                      {item.sender ||
                        "Unknown sender"}
                    </div>
                  </div>

                  <button
                    type="button"
                    className="feature-button feature-button--link"
                    onClick={() =>
                      onToggleSelection?.(
                        item.emailId,
                      )
                    }
                    disabled={
                      controlsDisabled
                    }
                  >
                    Remove
                  </button>
                </div>
              ),
            )}
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* EMPTY QUEUE                                         */}
      {/* ==================================================== */}

      {selectedItems.length === 0 && (
        <div className="feature-extraction-queue__empty">
          <strong>
            No emails selected
          </strong>

          <span>
            Select one or more parsed emails to begin
            feature extraction.
          </span>
        </div>
      )}
    </section>
  );
}
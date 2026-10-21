import React, {
  useMemo,
  useState,
} from "react";
import { Eye } from "lucide-react";

import {
  FEATURE_STATUS,
  getFeatureStatusLabel,
} from "../types";


// ============================================================
// STATUS BADGE
// ============================================================

function StatusBadge({
  status,
}) {
  const [expandedCells, setExpandedCells] = useState({});
  const toggleCell = (key) => setExpandedCells((current) => ({
    ...current,
    [key]: !current[key],
  }));
  const normalizedStatus =
    status ||
    FEATURE_STATUS.PENDING;

  return (
    <span
      className={
        "feature-status-badge " +
        `feature-status-badge--${normalizedStatus}`
      }
    >
      {getFeatureStatusLabel(
        normalizedStatus,
      )}
    </span>
  );
}


// ============================================================
// LEVEL BADGE
// ============================================================

function LevelBadge({
  level,
}) {
  const normalizedLevel =
    String(
      level || "normal",
    ).toLowerCase();

  const label =
    normalizedLevel === "bombing"
      ? "Bombing"
      : normalizedLevel === "normal"
        ? "Normal"
        : "Unknown";

  return (
    <span
      className={
        "feature-level-badge " +
        `feature-level-badge--${normalizedLevel}`
      }
    >
      {label}
    </span>
  );
}


// ============================================================
// SOURCE LABEL
// ============================================================

function getSourceLabel(
  item,
) {
  if (
    item?.sourceLabel
  ) {
    return item.sourceLabel;
  }

  if (
    item?.source
  ) {
    return item.source;
  }

  if (
    item?.sourceIdentifier
  ) {
    return item.sourceIdentifier;
  }

  return "Unknown";
}


// ============================================================
// RECEIVED DATE
// ============================================================

function formatReceivedAt(
  value,
) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return String(value);
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


// ============================================================
// EMPTY STATE
// ============================================================

function EmptyState() {
  return (
    <div
      className="feature-table__empty"
    >
      No parsed emails are available
      for feature engineering.
    </div>
  );
}


// ============================================================
// LOADING STATE
// ============================================================

function LoadingState() {
  return (
    <div
      className="feature-table__state"
      role="status"
      aria-live="polite"
    >
      Loading feature workspace…
    </div>
  );
}


// ============================================================
// MAIN COMPONENT
// ============================================================
//
// IMPORTANT:
//
// FeatureTable is intentionally responsible ONLY for:
//
//   • displaying rows
//   • current-page selection
//   • opening the parent-controlled details drawer
//
// It does NOT contain:
//
//   • Select All Matching
//   • Clear Selection toolbar
//   • Extract Selected
//   • Extract All Pending
//   • Feature details drawer
//
// Global selection/action controls belong to
// FeatureWorkspace.jsx.
// ============================================================

export default function FeatureTable({
  items = [],

  selectedEmailIds = new Set(),

  onToggleSelection,
  onSelectCurrentPage,
  onViewDetails,

  loading = false,
  disabled = false,

  showSelection = true,
}) {

  // ==========================================================
  // NORMALIZE SELECTION
  // ==========================================================

  const selectedIds =
    useMemo(() => {

      if (
        selectedEmailIds instanceof Set
      ) {
        return selectedEmailIds;
      }

      if (
        Array.isArray(
          selectedEmailIds,
        )
      ) {
        return new Set(
          selectedEmailIds,
        );
      }

      return new Set();

    }, [
      selectedEmailIds,
    ]);


  // ==========================================================
  // CURRENT PAGE SELECTABLE ITEMS
  // ==========================================================
  //
  // Only parsed emails can be selected for
  // feature extraction.
  //
  // Extracted records remain visible but are
  // no longer selectable.
  // ==========================================================

  const selectableItems =
    useMemo(
      () =>
        items.filter(
          (item) => {

            const parsed =
              item?.parsed === true ||
              item?.isParsed === true;

            const status =
              item?.featureStatus ||
              item?.status ||
              FEATURE_STATUS.PENDING;

            return (
              parsed &&
              status !==
                FEATURE_STATUS.EXTRACTED
            );
          },
        ),
      [
        items,
      ],
    );


  // ==========================================================
  // CURRENT PAGE SELECTION STATE
  // ==========================================================

  const allCurrentPageSelected =
    selectableItems.length > 0 &&
    selectableItems.every(
      (item) =>
        selectedIds.has(
          item.emailId,
        ),
    );


  const someCurrentPageSelected =
    selectableItems.some(
      (item) =>
        selectedIds.has(
          item.emailId,
        ),
    );


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <LoadingState />
    );
  }


  // ==========================================================
  // EMPTY
  // ==========================================================

  if (
    items.length === 0
  ) {
    return (
      <EmptyState />
    );
  }


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div
      className="feature-table-container"
    >

      {/* ==================================================== */}
      {/* TABLE WRAPPER                                         */}
      {/* ==================================================== */}

      <div
        className="feature-table-wrapper"
      >

        <table
          className="feature-table"
        >

          {/* ================================================= */}
          {/* TABLE HEADER                                      */}
          {/* ================================================= */}

          <thead>

            <tr>

              {/* ============================================= */}
              {/* SELECT                                        */}
              {/* ============================================= */}

              {showSelection && (
                <th
                  scope="col"
                  className={
                    "feature-table__select-column"
                  }
                >

                  <input
                    type="checkbox"
                    checked={
                      allCurrentPageSelected
                    }

                    /*
                     * React does not support an
                     * indeterminate checkbox through
                     * JSX alone, so the mixed state is
                     * represented through aria.
                     */
                    aria-checked={
                      someCurrentPageSelected &&
                      !allCurrentPageSelected
                        ? "mixed"
                        : allCurrentPageSelected
                          ? "true"
                          : "false"
                    }

                    aria-label={
                      allCurrentPageSelected
                        ? "Clear current page selection"
                        : "Select all selectable emails on this page"
                    }

                    onChange={() =>
                      onSelectCurrentPage?.(
                        selectableItems.map(
                          (item) =>
                            item.emailId,
                        ),
                      )
                    }

                    disabled={
                      disabled ||
                      selectableItems.length ===
                        0
                    }
                  />

                </th>
              )}


              {/* ============================================= */}
              {/* SUBJECT                                       */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__subject-column"
                }
              >
                Subject
              </th>


              {/* ============================================= */}
              {/* SENDER                                        */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__sender-column"
                }
              >
                Sender
              </th>


              {/* ============================================= */}
              {/* SOURCE                                        */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__source-column"
                }
              >
                Source
              </th>


              {/* ============================================= */}
              {/* LEVEL                                         */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__level-column"
                }
              >
                Level
              </th>


              {/* ============================================= */}
              {/* RECEIVED                                      */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__received-column"
                }
              >
                Received
              </th>


              {/* ============================================= */}
              {/* STATUS                                        */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__status-column"
                }
              >
                Status
              </th>


              {/* ============================================= */}
              {/* ACTION                                        */}
              {/* ============================================= */}

              <th
                scope="col"
                className={
                  "feature-table__action-column"
                }
              >
                Action
              </th>

            </tr>

          </thead>


          {/* ================================================= */}
          {/* TABLE BODY                                        */}
          {/* ================================================= */}

          <tbody>

            {items.map(
              (item) => {

                const emailId =
                  item?.emailId;

                const parsed =
                  item?.parsed === true ||
                  item?.isParsed === true;

                const featureStatus =
                  item?.featureStatus ||
                  item?.status ||
                  FEATURE_STATUS.PENDING;

                const selectable =
                  parsed &&
                  featureStatus !==
                    FEATURE_STATUS.EXTRACTED;

                const selected =
                  selectedIds.has(
                    emailId,
                  );


                const level =
                  item?.level ||
                  item?.groundTruthLabel ||
                  item?.groundTruth ||
                  "normal";


                const source =
                  getSourceLabel(
                    item,
                  );


                const receivedAt =
                  item?.receivedAt ||
                  item?.received_at;


                return (
                  <tr
                    key={
                      emailId
                    }
                    className={
                      selected
                        ? "feature-table__row--selected"
                        : ""
                    }
                  >

                    {/* ===================================== */}
                    {/* SELECT                                  */}
                    {/* ===================================== */}

                    {showSelection && (
                      <td
                        className={
                          "feature-table__select-column"
                        }
                      >

                        <input
                          type="checkbox"
                          checked={
                            selected
                          }

                          disabled={
                            disabled ||
                            !selectable
                          }

                          onChange={() =>
                            onToggleSelection?.(
                              emailId,
                            )
                          }

                          aria-label={
                            `Select ${
                              item?.subject ||
                              "email"
                            }`
                          }
                        />

                      </td>
                    )}


                    {/* ===================================== */}
                    {/* SUBJECT                                 */}
                    {/* ===================================== */}
                    {/*
                     *
                     * IMPORTANT:
                     *
                     * Message-ID is intentionally NOT
                     * rendered here.
                     *
                     * This keeps the subject column clean
                     * and prevents long technical identifiers
                     * from pushing/wrapping the subject.
                     *
                     */}

                    <td
                      className={
                        "feature-table__subject-column"
                      }
                    >

                      <button type="button" className={`email-table-cell-value email-table-subject${expandedCells[`${emailId}-subject`] ? " is-expanded" : ""}`} title={item?.subject || "No subject"} onClick={() => toggleCell(`${emailId}-subject`)}>
                        {item?.subject ||
                          "No subject"}
                      </button>

                    </td>


                    {/* ===================================== */}
                    {/* SENDER                                  */}
                    {/* ===================================== */}

                    <td
                      className={
                        "feature-table__sender-column"
                      }
                    >

                      <button type="button" className={`email-table-cell-value email-table-sender${expandedCells[`${emailId}-sender`] ? " is-expanded" : ""}`} title={item?.sender || "Unknown sender"} onClick={() => toggleCell(`${emailId}-sender`)}>
                        {item?.sender ||
                          "Unknown sender"}
                      </button>

                    </td>


                    {/* ===================================== */}
                    {/* SOURCE                                  */}
                    {/* ===================================== */}

                    <td
                      className={
                        "feature-table__source-column"
                      }
                    >

                      <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-source`] ? " is-expanded" : ""}`} title={source} onClick={() => toggleCell(`${emailId}-source`)}><span className="feature-source">{source}</span></button>

                      {item?.sourceIdentifier && (
                        <div
                          className={
                            "feature-table__secondary-text"
                          }
                          title={
                            item.sourceIdentifier
                          }
                        >
                          {
                            item.sourceIdentifier
                          }
                        </div>
                      )}

                    </td>


                    {/* ===================================== */}
                    {/* LEVEL                                   */}
                    {/* ===================================== */}

                    <td
                      className={
                        "feature-table__level-column"
                      }
                    >

                      <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-level`] ? " is-expanded" : ""}`} title={String(level)} onClick={() => toggleCell(`${emailId}-level`)}><LevelBadge level={level} /></button>

                    </td>


                    {/* ===================================== */}
                    {/* RECEIVED                                */}
                    {/* ===================================== */}

                    <td
                      className={
                        "feature-table__received-column"
                      }
                    >

                      <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-received`] ? " is-expanded" : ""}`} title={formatReceivedAt(receivedAt)} onClick={() => toggleCell(`${emailId}-received`)}>{formatReceivedAt(receivedAt)}</button>

                    </td>


                    {/* ===================================== */}
                    {/* STATUS                                  */}
                    {/* ===================================== */}

                    <td
                      className={
                        "feature-table__status-column"
                      }
                    >

                      <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-status`] ? " is-expanded" : ""}`} title={getFeatureStatusLabel(parsed ? featureStatus : FEATURE_STATUS.PENDING)} onClick={() => toggleCell(`${emailId}-status`)}><StatusBadge status={parsed ? featureStatus : FEATURE_STATUS.PENDING} /></button>

                    </td>


                    {/* ===================================== */}
                    {/* ACTION                                  */}
                    {/* ===================================== */}

                    <td
                      className={
                        "feature-table__action-column"
                      }
                    >

                      <button
                        type="button"
                        className="email-view-link"

                        onClick={() =>
                          onViewDetails?.(
                            emailId,
                            item,
                          )
                        }

                        disabled={
                          disabled
                        }

                        aria-label={
                          `View ${
                            item?.subject ||
                            "email"
                          }`
                        }
                      >
                        <Eye size={16} aria-hidden="true" />
                        <span>View</span>
                      </button>

                    </td>

                  </tr>
                );
              },
            )}

          </tbody>

        </table>

      </div>

    </div>
  );
}

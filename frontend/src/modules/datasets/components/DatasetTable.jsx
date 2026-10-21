
import React, { useMemo } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Inbox,
} from "lucide-react";
import {
  DATASET_LABELS,
  DATASET_SOURCES,
  WORKSPACE_PAGE_SIZE,
} from "../types";

/**
 * Dataset Management — Workspace Table
 *
 * Responsibilities:
 * - Render the current page of eligible emails.
 * - Select or deselect individual rows.
 * - Select or deselect all rows on the current page.
 * - Open an email's details through the parent callback.
 * - Navigate through server-paginated results.
 *
 * Select All Matching is intentionally handled by
 * DatasetSelectionBar / the parent page, not this table.
 */

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function getGroundTruthLabel(value) {
  if (value === DATASET_LABELS.NORMAL) {
    return "Normal";
  }

  if (value === DATASET_LABELS.BOMBING) {
    return "Bombing";
  }

  return "Unknown";
}

function getSourceLabel(value) {
  if (value === DATASET_SOURCES.RAW_EMAIL) {
    return "Raw Email";
  }

  if (value === DATASET_SOURCES.FILE_UPLOAD) {
    return "File Upload";
  }

  return "Unknown";
}

function getEmailId(email) {
  return email?.id ?? email?.email_id ?? "";
}

export default function DatasetTable({
  items = [],
  selectedIds = [],
  onSelectionChange,
  onView,
  page = 1,
  pageSize = WORKSPACE_PAGE_SIZE,
  total = 0,
  totalPages,
  onPageChange,
  loading = false,
  disabled = false,
  canSelect = true,
  className = "",
}) {
  const selectedSet = useMemo(
    () => new Set(selectedIds),
    [selectedIds]
  );

  const validItems = useMemo(
    () => items.filter((item) => Boolean(getEmailId(item))),
    [items]
  );

  const currentPageIds = useMemo(
    () => validItems.map(getEmailId),
    [validItems]
  );

  const selectedOnPage = currentPageIds.filter((id) =>
    selectedSet.has(id)
  ).length;

  const allPageSelected =
    currentPageIds.length > 0 &&
    selectedOnPage === currentPageIds.length;

  const somePageSelected =
    selectedOnPage > 0 && !allPageSelected;

  const resolvedTotalPages =
    totalPages ??
    Math.max(1, Math.ceil(Number(total || 0) / Number(pageSize || 1)));

  const safePage = Math.min(
    Math.max(1, Number(page) || 1),
    Math.max(1, resolvedTotalPages)
  );

  const start = total === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const end = Math.min(safePage * pageSize, total);

  const toggleRow = (id, checked) => {
    if (!id || disabled) {
      return;
    }

    const next = new Set(selectedSet);

    if (checked) {
      next.add(id);
    } else {
      next.delete(id);
    }

    onSelectionChange?.([...next]);
  };

  const toggleCurrentPage = (checked) => {
    if (disabled) {
      return;
    }

    const next = new Set(selectedSet);

    currentPageIds.forEach((id) => {
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
    });

    onSelectionChange?.([...next]);
  };

  const handlePrevious = () => {
    if (safePage > 1) {
      onPageChange?.(safePage - 1);
    }
  };

  const handleNext = () => {
    if (safePage < resolvedTotalPages) {
      onPageChange?.(safePage + 1);
    }
  };

  return (
    <section
      className={`dataset-table-section ${className}`.trim()}
      aria-label="Feature-extracted emails"
    >
      <div className="dataset-table-container">
        <table className="dataset-table">
          <thead>
            <tr>
              {canSelect && <th className="dataset-table__checkbox-column">
                <input
                  type="checkbox"
                  aria-label="Select all emails on this page"
                  checked={allPageSelected}
                  ref={(element) => {
                    if (element) {
                      element.indeterminate = somePageSelected;
                    }
                  }}
                  onChange={(event) =>
                    toggleCurrentPage(event.target.checked)
                  }
                  disabled={disabled || loading || currentPageIds.length === 0}
                />
              </th>}
              <th scope="col">Subject</th>
              <th scope="col">Sender</th>
              <th scope="col">Ground Truth</th>
              <th scope="col">Source</th>
              <th scope="col">Received</th>
              <th scope="col" className="dataset-table__action-column">
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={canSelect ? 7 : 6} className="dataset-table__state">
                  <span
                    className="dataset-spinner"
                    aria-hidden="true"
                  />
                  <span>Loading eligible emails...</span>
                </td>
              </tr>
            ) : validItems.length === 0 ? (
              <tr>
                <td colSpan={canSelect ? 7 : 6} className="dataset-table__state">
                  <div className="dataset-empty-state">
                    <Inbox size={30} aria-hidden="true" />
                    <strong>No eligible emails found</strong>
                    <span>
                      Try changing the filters or check whether emails
                      have been parsed and feature-extracted.
                    </span>
                  </div>
                </td>
              </tr>
            ) : (
              validItems.map((email) => {
                const id = getEmailId(email);
                const isSelected = selectedSet.has(id);
                const groundTruth = email.ground_truth;
                const source = email.source;

                return (
                  <tr
                    key={id}
                    className={
                      isSelected
                        ? "dataset-table__row dataset-table__row--selected"
                        : "dataset-table__row"
                    }
                  >
                    {canSelect && <td className="dataset-table__checkbox-column">
                      <input
                        type="checkbox"
                        aria-label={`Select email ${email.subject || id}`}
                        checked={isSelected}
                        onChange={(event) =>
                          toggleRow(id, event.target.checked)
                        }
                        disabled={disabled}
                      />
                    </td>}

                    <td className="dataset-table__subject">
                      <span title={email.subject || "Untitled email"}>
                        {email.subject || "Untitled email"}
                      </span>
                    </td>

                    <td className="dataset-table__sender">
                      <span title={email.sender || ""}>
                        {email.sender || "—"}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`dataset-label dataset-label--${
                          groundTruth === DATASET_LABELS.NORMAL
                            ? "normal"
                            : groundTruth === DATASET_LABELS.BOMBING
                              ? "bombing"
                              : "unknown"
                        }`}
                      >
                        {getGroundTruthLabel(groundTruth)}
                      </span>
                    </td>

                    <td>
                      <span className="dataset-table__source">
                        {getSourceLabel(source)}
                      </span>
                    </td>

                    <td className="dataset-table__date">
                      {formatDate(email.received_at)}
                    </td>

                    <td className="dataset-table__action-column">
                      <button
                        type="button"
                        className="dataset-button dataset-button--ghost"
                        onClick={() => onView?.(email)}
                        disabled={disabled}
                        aria-label={`View details for ${email.subject || id}`}
                      >
                        <Eye size={16} aria-hidden="true" />
                        <span>View</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="dataset-table-pagination">
        <div className="dataset-table-pagination__summary">
          {loading
            ? "Loading..."
            : `${start} - ${end} / Total ${Number(total || 0).toLocaleString()}`}
        </div>

        <div className="dataset-table-pagination__controls">
          <button
            type="button"
            className="dataset-button dataset-button--secondary"
            onClick={handlePrevious}
            disabled={disabled || loading || safePage <= 1}
            aria-label="Previous page"
          >
            <ChevronLeft size={16} aria-hidden="true" />
            <span>Previous</span>
          </button>

          <span className="dataset-table-pagination__page">
            Page {safePage} of {resolvedTotalPages}
          </span>

          <button
            type="button"
            className="dataset-button dataset-button--secondary"
            onClick={handleNext}
            disabled={
              disabled || loading || safePage >= resolvedTotalPages
            }
            aria-label="Next page"
          >
            <span>Next</span>
            <ChevronRight size={16} aria-hidden="true" />
          </button>
        </div>
      </div>
    </section>
  );
}

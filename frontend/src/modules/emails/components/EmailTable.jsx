import { useState } from "react";
import { Eye } from "lucide-react";
import {
  getEmailGroundTruthLabel,
  getEmailSourceLabel,
} from "../types";


// ============================================================
// DATE FORMATTER
// ============================================================

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}


// ============================================================
// GROUND-TRUTH STATUS BADGE
// ============================================================
//
// IMPORTANT:
// The Email Management "Status" column represents the
// user-provided ground-truth label.
//
// It does NOT represent:
//   - ML prediction
//   - confidence
//   - risk
//   - threat level
//

function StatusBadge({ status }) {
  const normalizedStatus = String(
    status || "unknown",
  ).toLowerCase();

  const label =
    getEmailGroundTruthLabel(
      normalizedStatus,
    );

  return (
    <span
      className={`email-status-badge email-status-${normalizedStatus}`}
    >
      {label}
    </span>
  );
}


// ============================================================
// EMAIL TABLE
// ============================================================

export default function EmailTable({
  emails = [],
  loading = false,
  error = "",
  emptyMessage = "No emails have been added yet.",
  onRetry,
  onView,
}) {
  const [expandedCells, setExpandedCells] = useState({});
  const toggleCell = (key) => setExpandedCells((current) => ({
    ...current,
    [key]: !current[key],
  }));
  // ==========================================================
  // LOADING STATE
  // ==========================================================

  if (loading) {
    return (
      <div
        className="email-table-state"
        role="status"
        aria-live="polite"
        aria-label="Loading emails"
      >
        <div
          className="email-loading-indicator"
          aria-hidden="true"
        />

        <span>
          Loading emails...
        </span>
      </div>
    );
  }


  // ==========================================================
  // ERROR STATE
  // ==========================================================

  if (error) {
    return (
      <div
        className="email-table-state email-table-error"
        role="alert"
      >
        <strong>
          Unable to load emails.
        </strong>

        <span>
          {error}
        </span>

        {onRetry && (
          <button
            type="button"
            className="email-secondary-button"
            onClick={onRetry}
          >
            Try Again
          </button>
        )}
      </div>
    );
  }


  // ==========================================================
  // EMPTY STATE
  // ==========================================================

  if (!emails.length) {
    return (
      <div className="email-table-state">
        <div
          className="email-empty-icon"
          aria-hidden="true"
        >
          ✉
        </div>

        <strong>
          No emails found
        </strong>

        <span>
          {emptyMessage}
        </span>
      </div>
    );
  }


  // ==========================================================
  // EMAIL TABLE
  // ==========================================================

  return (
    <div className="email-table-wrapper">
      <table className="email-table">
        <thead>
          <tr>
            <th scope="col">
              Subject
            </th>

            <th scope="col">
              Sender
            </th>

            <th scope="col">
              Source
            </th>

            <th scope="col">
              Received
            </th>

            <th scope="col">
              Status
            </th>

            <th scope="col">
              Action
            </th>
          </tr>
        </thead>

        <tbody>
          {emails.map((email) => {
            const emailId =
              email?.id;

            const subject =
              email?.subject ||
              "(No subject)";

            const sender =
              email?.sender ||
              "Unknown";

            const sourceLabel =
              getEmailSourceLabel(
                email?.source,
              );

            const groundTruthLabel =
              email?.ground_truth_label;


            return (
              <tr
                key={emailId}
              >
                {/* ==================================================
                    SUBJECT
                    ================================================== */}

                <td>
                  <button type="button" className={`email-table-cell-value email-table-subject${expandedCells[`${emailId}-subject`] ? " is-expanded" : ""}`} title={subject} onClick={() => toggleCell(`${emailId}-subject`)}>
                    {subject}
                  </button>

                  {email?.message_id && (
                    <button type="button" className={`email-table-cell-value email-table-message-id${expandedCells[`${emailId}-message-id`] ? " is-expanded" : ""}`} title={email.message_id} onClick={() => toggleCell(`${emailId}-message-id`)}>
                      {email.message_id}
                    </button>
                  )}
                </td>


                {/* ==================================================
                    SENDER
                    ================================================== */}

                <td>
                  <button type="button" className={`email-table-cell-value email-table-sender${expandedCells[`${emailId}-sender`] ? " is-expanded" : ""}`} title={sender} onClick={() => toggleCell(`${emailId}-sender`)}>
                    {sender}
                  </button>
                </td>


                {/* ==================================================
                    SOURCE
                    ================================================== */}

                <td>
                  <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-source`] ? " is-expanded" : ""}`} title={sourceLabel} onClick={() => toggleCell(`${emailId}-source`)}>
                    <span className="email-source-badge">{sourceLabel}</span>
                  </button>
                </td>


                {/* ==================================================
                    RECEIVED
                    ================================================== */}

                <td>
                  <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-received`] ? " is-expanded" : ""}`} title={formatDate(email?.received_at)} onClick={() => toggleCell(`${emailId}-received`)}>{formatDate(email?.received_at)}</button>
                </td>


                {/* ==================================================
                    GROUND TRUTH STATUS
                    ================================================== */}

                <td>
                  <button type="button" className={`email-table-cell-value${expandedCells[`${emailId}-status`] ? " is-expanded" : ""}`} title={getEmailGroundTruthLabel(String(groundTruthLabel || "unknown").toLowerCase())} onClick={() => toggleCell(`${emailId}-status`)}><StatusBadge status={groundTruthLabel} /></button>
                </td>


                {/* ==================================================
                    ACTION
                    ================================================== */}

                <td>
                  <button
                    type="button"
                    className="email-view-link"
                    onClick={() =>
                      onView?.(email)
                    }
                    disabled={!emailId}
                    aria-label={`View email ${subject}`}
                  >
                    <Eye size={15} aria-hidden="true" />
                    View
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

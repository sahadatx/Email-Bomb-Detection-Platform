import { useMemo } from "react";
import { Eye } from "lucide-react";

import {
  EMAIL_LEVEL,
  EMAIL_SOURCE,
  PARSING_STATUS,
} from "../types";


// ============================================================================
// DATE FORMATTER
// ============================================================================

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
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


// ============================================================================
// SOURCE LABEL
// ============================================================================

function getSourceLabel(source) {
  switch (source) {
    case EMAIL_SOURCE.RAW_EMAIL:
      return "Raw Email";

    case EMAIL_SOURCE.FILE_UPLOAD:
      return "File Upload";

    case EMAIL_SOURCE.IMAP:
      return "IMAP";

    default:
      if (!source) {
        return "—";
      }

      return String(source)
        .replaceAll("_", " ")
        .replace(
          /\b\w/g,
          (character) =>
            character.toUpperCase(),
        );
  }
}


// ============================================================================
// LEVEL LABEL
// ============================================================================

function getLevelLabel(level) {
  switch (level) {
    case EMAIL_LEVEL.NORMAL:
      return "Normal";

    case EMAIL_LEVEL.BOMBING:
      return "Bombing";

    default:
      return "—";
  }
}


// ============================================================================
// LEVEL CLASS
// ============================================================================

function getLevelClass(level) {
  switch (level) {
    case EMAIL_LEVEL.NORMAL:
      return "parsing-level parsing-level--normal";

    case EMAIL_LEVEL.BOMBING:
      return "parsing-level parsing-level--bombing";

    default:
      return "parsing-level";
  }
}


// ============================================================================
// STATUS LABEL
// ============================================================================

function getStatusLabel(status) {
  switch (status) {
    case PARSING_STATUS.PARSED:
      return "Parsed";

    case PARSING_STATUS.WARNING:
      return "Warning";

    case PARSING_STATUS.FAILED:
      return "Failed";

    case PARSING_STATUS.PENDING:
    default:
      return "Pending";
  }
}


// ============================================================================
// STATUS CLASS
// ============================================================================

function getStatusClass(status) {
  switch (status) {
    case PARSING_STATUS.PARSED:
      return "parsing-status parsing-status--parsed";

    case PARSING_STATUS.WARNING:
      return "parsing-status parsing-status--warning";

    case PARSING_STATUS.FAILED:
      return "parsing-status parsing-status--failed";

    case PARSING_STATUS.PENDING:
    default:
      return "parsing-status parsing-status--pending";
  }
}


// ============================================================================
// EMAIL ID
// ============================================================================

function getEmailId(email) {
  return (
    email?.email_id ??
    email?.id ??
    null
  );
}


// ============================================================================
// PARSING STATUS
// ============================================================================

function getParsingStatus(email) {
  return (
    email?.parsing_status ??
    PARSING_STATUS.PENDING
  );
}


// ============================================================================
// EMAIL LEVEL
// ============================================================================

function getEmailLevel(email) {
  return (
    email?.level ??
    null
  );
}


// ============================================================================
// SUBJECT
// ============================================================================

function getSubject(email) {
  return (
    email?.subject ||
    "(No subject)"
  );
}


// ============================================================================
// SENDER
// ============================================================================

function getSender(email) {
  return (
    email?.sender ||
    "Unknown sender"
  );
}


// ============================================================================
// SOURCE
// ============================================================================

function getSource(email) {
  return (
    email?.source ??
    null
  );
}


// ============================================================================
// OPEN EMAIL DETAILS
// ============================================================================

/**
 * The table does not own navigation.
 *
 * The parent workspace owns the parsed-email
 * drawer state and is responsible for loading
 * the full parsed-email details.
 *
 * Flow:
 *
 *     View
 *       ↓
 *     onOpenEmail(email)
 *       ↓
 *     ParsingWorkspace
 *       ↓
 *     getParsedEmail(email_id)
 *       ↓
 *     ParsedEmailDrawer
 */
function openEmailDetails(
  email,
  onOpenEmail,
) {
  const emailId =
    getEmailId(email);

  if (
    !emailId ||
    typeof onOpenEmail !==
      "function"
  ) {
    return;
  }

  onOpenEmail(email);
}


// ============================================================================
// KEYBOARD VIEW HANDLER
// ============================================================================

function handleViewKeyDown(
  event,
  email,
  onOpenEmail,
) {
  if (
    event.key !== "Enter" &&
    event.key !== " "
  ) {
    return;
  }

  event.preventDefault();

  openEmailDetails(
    email,
    onOpenEmail,
  );
}


// ============================================================================
// COMPONENT
// ============================================================================

export default function ParsingEmailTable({
  emails = [],
  selectedIds = [],
  loading = false,
  allSelected = false,
  onSelectAll,
  onToggleSelection,
  onOpenEmail,
  canSelect = true,
}) {
  // ==========================================================================
  // SELECTED ID SET
  // ==========================================================================

  const selectedSet = useMemo(
    () =>
      new Set(
        selectedIds,
      ),
    [selectedIds],
  );


  // ==========================================================================
  // CURRENT PAGE SELECTABLE IDS
  // ==========================================================================

  const selectableIds = useMemo(
    () =>
      emails
        .map(
          getEmailId,
        )
        .filter(Boolean),
    [emails],
  );


  // ==========================================================================
  // CURRENT PAGE SELECTED COUNT
  // ==========================================================================

  const currentPageSelectedCount =
    useMemo(
      () =>
        selectableIds.filter(
          (id) =>
            selectedSet.has(
              id,
            ),
        ).length,
      [
        selectableIds,
        selectedSet,
      ],
    );


  // ==========================================================================
  // CURRENT PAGE FULL SELECTION
  // ==========================================================================

  const isCurrentPageFullySelected =
    selectableIds.length > 0 &&
    currentPageSelectedCount ===
      selectableIds.length;


  // ==========================================================================
  // LOADING STATE
  // ==========================================================================

  if (loading) {
    return (
      <section
        className="parsing-table-card"
      >
        <div
          className="parsing-table-state"
          role="status"
          aria-live="polite"
        >
          <span
            className="parsing-loading-indicator"
            aria-hidden="true"
          />

          <span>
            Loading parsing workspace...
          </span>
        </div>
      </section>
    );
  }


  // ==========================================================================
  // EMPTY STATE
  // ==========================================================================

  if (!emails.length) {
    return (
      <section
        className="parsing-table-card"
      >
        <div
          className="parsing-table-state"
        >
          <strong>
            No emails found.
          </strong>

          <span>
            No collected emails match
            the current filters.
          </span>
        </div>
      </section>
    );
  }


  // ==========================================================================
  // TABLE
  // ==========================================================================

  return (
    <section
      className="parsing-table-card"
    >

      {/* ================================================================== */}
      {/* TABLE HEADER */}
      {/* ================================================================== */}

      <div
        className="parsing-table-card__header"
      >
        <div>
          <h2>
            Email Parsing Workspace
          </h2>

          <span>
            {emails.length} email
            {emails.length === 1
              ? ""
              : "s"} on this page
          </span>
        </div>
      </div>


      {/* ================================================================== */}
      {/* TABLE WRAPPER */}
      {/* ================================================================== */}

      <div
        className="parsing-table-wrapper"
      >
        <table
          className="parsing-email-table"
        >

          {/* ============================================================ */}
          {/* TABLE HEAD */}
          {/* ============================================================ */}

          <thead>
            <tr>

              {/* ------------------------------------------------------ */}
              {/* SELECT */}
              {/* ------------------------------------------------------ */}

              {canSelect && <th
                scope="col"
                className="parsing-email-table__select-column"
              >
                <input
                  type="checkbox"
                  aria-label="Select all emails on this page"
                  checked={
                    allSelected ||
                    isCurrentPageFullySelected
                  }
                  ref={(element) => {
                    if (!element) {
                      return;
                    }

                    element.indeterminate =
                      currentPageSelectedCount >
                        0 &&
                      currentPageSelectedCount <
                        selectableIds.length;
                  }}
                  disabled={
                    selectableIds.length ===
                    0
                  }
                  onChange={() =>
                    onSelectAll?.()
                  }
                />
              </th>}


              {/* ------------------------------------------------------ */}
              {/* SUBJECT */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Subject
              </th>


              {/* ------------------------------------------------------ */}
              {/* SENDER */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Sender
              </th>


              {/* ------------------------------------------------------ */}
              {/* SOURCE */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Source
              </th>


              {/* ------------------------------------------------------ */}
              {/* LEVEL */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Level
              </th>


              {/* ------------------------------------------------------ */}
              {/* RECEIVED */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Received
              </th>


              {/* ------------------------------------------------------ */}
              {/* STATUS */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Status
              </th>


              {/* ------------------------------------------------------ */}
              {/* ACTION */}
              {/* ------------------------------------------------------ */}

              <th scope="col">
                Action
              </th>

            </tr>
          </thead>


          {/* ============================================================ */}
          {/* TABLE BODY */}
          {/* ============================================================ */}

          <tbody>

            {emails.map(
              (email) => {
                const emailId =
                  getEmailId(
                    email,
                  );

                const subject =
                  getSubject(
                    email,
                  );

                const sender =
                  getSender(
                    email,
                  );

                const source =
                  getSource(
                    email,
                  );

                const level =
                  getEmailLevel(
                    email,
                  );

                const parsingStatus =
                  getParsingStatus(
                    email,
                  );

                const isSelected =
                  Boolean(
                    emailId,
                  ) &&
                  selectedSet.has(
                    emailId,
                  );

                const rowKey =
                  emailId ??
                  `${subject}-${email?.received_at ?? ""}`;


                return (
                  <tr
                    key={
                      rowKey
                    }
                    className={
                      isSelected
                        ? "parsing-email-table__row parsing-email-table__row--selected"
                        : "parsing-email-table__row"
                    }
                  >

                    {/* ================================================== */}
                    {/* SELECT */}
                    {/* ================================================== */}

                    {canSelect && <td
                      className="parsing-email-table__select-cell"
                    >
                      <input
                        type="checkbox"
                        aria-label={`Select ${subject}`}
                        checked={
                          isSelected
                        }
                        disabled={
                          !emailId
                        }
                        onChange={() =>
                          onToggleSelection?.(
                            emailId,
                          )
                        }
                      />
                    </td>}


                    {/* ================================================== */}
                    {/* SUBJECT */}
                    {/* ================================================== */}

                    <td>
                      <div
                        className="parsing-email-subject"
                      >
                        <strong
                          className="parsing-email-subject__text"
                          title={
                            subject
                          }
                        >
                          {
                            subject
                          }
                        </strong>
                      </div>
                    </td>


                    {/* ================================================== */}
                    {/* SENDER */}
                    {/* ================================================== */}

                    <td>
                      <span
                        className="parsing-email-sender"
                        title={
                          sender
                        }
                      >
                        {
                          sender
                        }
                      </span>
                    </td>


                    {/* ================================================== */}
                    {/* SOURCE */}
                    {/* ================================================== */}

                    <td>
                      <span
                        className="parsing-source"
                        title={
                          getSourceLabel(
                            source,
                          )
                        }
                      >
                        {
                          getSourceLabel(
                            source,
                          )
                        }
                      </span>
                    </td>


                    {/* ================================================== */}
                    {/* LEVEL */}
                    {/* ================================================== */}

                    <td>
                      <span
                        className={
                          getLevelClass(
                            level,
                          )
                        }
                        aria-label={`Ground truth level: ${getLevelLabel(
                          level,
                        )}`}
                      >
                        {
                          getLevelLabel(
                            level,
                          )
                        }
                      </span>
                    </td>


                    {/* ================================================== */}
                    {/* RECEIVED */}
                    {/* ================================================== */}

                    <td>
                      <time
                        dateTime={
                          email?.received_at ||
                          undefined
                        }
                      >
                        {
                          formatDate(
                            email?.received_at,
                          )
                        }
                      </time>
                    </td>


                    {/* ================================================== */}
                    {/* STATUS */}
                    {/* ================================================== */}

                    <td>
                      <span
                        className={
                          getStatusClass(
                            parsingStatus,
                          )
                        }
                        aria-label={`Parsing status: ${getStatusLabel(
                          parsingStatus,
                        )}`}
                      >
                        {
                          getStatusLabel(
                            parsingStatus,
                          )
                        }
                      </span>
                    </td>


                    {/* ================================================== */}
                    {/* ACTION */}
                    {/* ================================================== */}

                    <td>
                      <button
                        type="button"
                        className="parsing-email-table__view-button"
                        disabled={
                          !emailId ||
                          parsingStatus === PARSING_STATUS.PENDING ||
                          typeof onOpenEmail !==
                            "function"
                        }
                        onClick={() =>
                          openEmailDetails(
                            email,
                            onOpenEmail,
                          )
                        }
                        onKeyDown={(event) =>
                          handleViewKeyDown(
                            event,
                            email,
                            onOpenEmail,
                          )
                        }
                        title={
                          !emailId
                            ? "Email details unavailable"
                            : parsingStatus === PARSING_STATUS.PENDING
                              ? "Parse this email before viewing structured details"
                              : "View parsed email details"
                        }
                      >
                        <Eye size={15} aria-hidden="true" />
                        View
                      </button>
                    </td>

                  </tr>
                );
              },
            )}

          </tbody>

        </table>
      </div>


      {/* ================================================================== */}
      {/* TABLE FOOTER */}
      {/* ================================================================== */}

      <div
        className="parsing-table-card__footer"
      >
        <span>
          {currentPageSelectedCount > 0
            ? `${currentPageSelectedCount} selected on this page`
            : "No emails selected on this page"}
        </span>

        {allSelected && (
          <span>
            All matching emails selected.
          </span>
        )}
      </div>

    </section>
  );
}

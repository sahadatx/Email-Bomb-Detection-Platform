import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useAuth } from "../../../core/auth/AuthProvider";

import {
  getParsingEmails,
  getParsingSummary,
  getMatchingEmailIds,
  getPendingEmailIds,
  getParsedEmail,
  parseEmails,
  parseAllPending,
  getParsingServiceErrorMessage,
} from "../services/parsingService";

import {
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,
  EMPTY_PERSISTENCE_SUMMARY,
  EMPTY_PAGINATION,
  PARSING_STATUS,
  createEmptyParsingFilters,
  normalizeParsingFilters,
} from "../types";

import ParsingEmailTable from "../components/ParsingEmailTable";
import ParsingStats from "../components/ParsingStats";
import ParsingQueue from "../components/ParsingQueue";
import ParsedEmailDrawer from "../components/ParsedEmailDrawer";


// ============================================================================
// Constants
// ============================================================================

const BATCH_SIZE = 100;


// ============================================================================
// Helpers
// ============================================================================

function getEmailId(email) {
  return (
    email?.email_id ??
    email?.id ??
    null
  );
}


function getParsingStatus(email) {
  return (
    email?.parsing_status ??
    PARSING_STATUS.PENDING
  );
}


function getQueueStatus(parsingStatus) {
  switch (parsingStatus) {
    case PARSING_STATUS.PARSED:
      return "parsed";

    case PARSING_STATUS.WARNING:
      return "warning";

    case PARSING_STATUS.FAILED:
      return "failed";

    case PARSING_STATUS.PENDING:
    default:
      return "processing";
  }
}


function getValidationMessage(result) {
  const errors =
    Array.isArray(
      result?.validation_errors,
    )
      ? result.validation_errors
      : Array.isArray(
          result?.validation?.errors,
        )
        ? result.validation.errors
        : [];

  const warnings =
    Array.isArray(
      result?.validation_warnings,
    )
      ? result.validation_warnings
      : Array.isArray(
          result?.validation?.warnings,
        )
        ? result.validation.warnings
        : [];

  if (errors.length > 0) {
    return errors.join(" ");
  }

  if (warnings.length > 0) {
    return warnings.join(" ");
  }

  return "";
}


function normalizePagination(response) {
  const total =
    Number(
      response?.total,
    ) || 0;

  const page =
    Number(
      response?.page,
    ) || DEFAULT_PAGE;

  const pageSize =
    Number(
      response?.page_size,
    ) || DEFAULT_PAGE_SIZE;

  const totalPages =
    Number(
      response?.total_pages,
    ) || 1;

  return {
    page: Math.max(
      DEFAULT_PAGE,
      page,
    ),

    page_size: Math.max(
      1,
      pageSize,
    ),

    total: Math.max(
      0,
      total,
    ),

    total_pages: Math.max(
      1,
      totalPages,
    ),

    start_index: Math.max(
      0,
      Number(
        response?.start_index,
      ) || 0,
    ),

    end_index: Math.max(
      0,
      Number(
        response?.end_index,
      ) || 0,
    ),
  };
}


function normalizeSummary(response) {
  return {
    total_collected:
      Math.max(
        0,
        Number(
          response?.total_collected,
        ) || 0,
      ),

    total_parsed:
      Math.max(
        0,
        Number(
          response?.total_parsed ??
          response?.parsed,
        ) || 0,
      ),

    total_pending:
      Math.max(
        0,
        Number(
          response?.total_pending ??
          response?.pending,
        ) || 0,
      ),

    total_warnings:
      Math.max(
        0,
        Number(
          response?.total_warnings ??
          response?.warnings,
        ) || 0,
      ),

    total_failed:
      Math.max(
        0,
        Number(
          response?.total_failed ??
          response?.failed,
        ) || 0,
      ),

    // Kept in state for backend compatibility.
    // Not displayed in Module 03 UI.
    ready_for_features:
      Math.max(
        0,
        Number(
          response?.ready_for_features,
        ) || 0,
      ),

    // Kept in state for backend compatibility.
    // Not displayed in Module 03 UI.
    readiness_percentage:
      Math.min(
        100,
        Math.max(
          0,
          Number(
            response?.readiness_percentage,
          ) || 0,
        ),
      ),
  };
}


function normalizeIdList(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  return [
    ...new Set(
      value
        .map((item) =>
          String(item).trim(),
        )
        .filter(Boolean),
    ),
  ];
}


function chunkArray(items, size) {
  const chunks = [];

  for (
    let index = 0;
    index < items.length;
    index += size
  ) {
    chunks.push(
      items.slice(
        index,
        index + size,
      ),
    );
  }

  return chunks;
}


// ============================================================================
// Page
// ============================================================================

export default function ParsingWorkspace() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  // ==========================================================================
  // Email list state
  // ==========================================================================

  const [emails, setEmails] =
    useState([]);

  const [page, setPage] =
    useState(
      DEFAULT_PAGE,
    );

  const [pagination, setPagination] =
    useState(
      EMPTY_PAGINATION,
    );


  // ==========================================================================
  // Filters
  // ==========================================================================

  const [filters, setFilters] =
    useState(
      createEmptyParsingFilters(),
    );


  // ==========================================================================
  // Global parsing summary
  // ==========================================================================

  const [summary, setSummary] =
    useState(
      EMPTY_PERSISTENCE_SUMMARY,
    );


  // ==========================================================================
  // Selection state
  // ==========================================================================

  const [selectedIds, setSelectedIds] =
    useState([]);

  const [
    allMatchingSelected,
    setAllMatchingSelected,
  ] = useState(false);


  // ==========================================================================
  // Parsing queue
  // ==========================================================================

  const [queue, setQueue] =
    useState([]);


  // ==========================================================================
  // Parsed Email Details Drawer
  // ==========================================================================

  const [
    parsedEmail,
    setParsedEmail,
  ] = useState(null);

  const [
    parsedEmailDrawerOpen,
    setParsedEmailDrawerOpen,
  ] = useState(false);

  const [
    parsedEmailLoading,
    setParsedEmailLoading,
  ] = useState(false);

  const [
    parsedEmailError,
    setParsedEmailError,
  ] = useState("");


  // ==========================================================================
  // UI state
  // ==========================================================================

  const [loading, setLoading] =
    useState(true);

  const [
    summaryLoading,
    setSummaryLoading,
  ] = useState(true);

  const [parsing, setParsing] =
    useState(false);

  const [
    pendingAllParsing,
    setPendingAllParsing,
  ] = useState(false);

  const [error, setError] =
    useState("");

  const [
    summaryError,
    setSummaryError,
  ] = useState("");

  const [
    selectionLoading,
    setSelectionLoading,
  ] = useState(false);


  // ==========================================================================
  // Request refs
  // ==========================================================================

  const listRequestId =
    useRef(0);

  const summaryRequestId =
    useRef(0);

  const detailRequestId =
    useRef(0);


  // ==========================================================================
  // Normalized filters
  // ==========================================================================

  const normalizedFilters =
    useMemo(
      () =>
        normalizeParsingFilters(
          filters,
        ),
      [filters],
    );


  // ==========================================================================
  // LOAD EMAILS
  // ==========================================================================

  const loadEmails =
    useCallback(
      async ({
        signal,
        targetPage = page,
        targetFilters = normalizedFilters,
      } = {}) => {
        const requestId =
          ++listRequestId.current;

        setLoading(true);
        setError("");

        try {
          const response =
            await getParsingEmails({
              page:
                targetPage,

              pageSize:
                DEFAULT_PAGE_SIZE,

              filters:
                targetFilters,

              signal,
            });

          if (
            requestId !==
            listRequestId.current
          ) {
            return;
          }

          const items =
            Array.isArray(
              response?.items,
            )
              ? response.items
              : [];

          setEmails(
            items,
          );

          setPagination(
            normalizePagination(
              response,
            ),
          );
        } catch (
          requestError
        ) {
          if (
            requestError?.name ===
            "AbortError"
          ) {
            return;
          }

          if (
            requestId !==
            listRequestId.current
          ) {
            return;
          }

          setError(
            getParsingServiceErrorMessage(
              requestError,
            ),
          );

          setEmails(
            [],
          );

          setPagination(
            EMPTY_PAGINATION,
          );
        } finally {
          if (
            !signal?.aborted &&
            requestId ===
              listRequestId.current
          ) {
            setLoading(
              false,
            );
          }
        }
      },
      [
        page,
        normalizedFilters,
      ],
    );


  // ==========================================================================
  // LOAD GLOBAL SUMMARY
  // ==========================================================================

  const loadSummary =
    useCallback(
      async ({
        signal,
      } = {}) => {
        const requestId =
          ++summaryRequestId.current;

        setSummaryLoading(
          true,
        );

        setSummaryError("");

        try {
          const response =
            await getParsingSummary({
              signal,
            });

          if (
            requestId !==
            summaryRequestId.current
          ) {
            return;
          }

          setSummary(
            normalizeSummary(
              response,
            ),
          );
        } catch (
          requestError
        ) {
          if (
            requestError?.name ===
            "AbortError"
          ) {
            return;
          }

          if (
            requestId !==
            summaryRequestId.current
          ) {
            return;
          }

          setSummaryError(
            getParsingServiceErrorMessage(
              requestError,
            ),
          );

          setSummary(
            EMPTY_PERSISTENCE_SUMMARY,
          );
        } finally {
          if (
            !signal?.aborted &&
            requestId ===
              summaryRequestId.current
          ) {
            setSummaryLoading(
              false,
            );
          }
        }
      },
      [],
    );


  // ==========================================================================
  // LOAD EMAILS WHEN PAGE OR FILTERS CHANGE
  // ==========================================================================

  useEffect(() => {
    const controller =
      new AbortController();

    loadEmails({
      signal:
        controller.signal,
    });

    return () => {
      controller.abort();
    };
  }, [
    loadEmails,
  ]);


  // ==========================================================================
  // INITIAL / SUMMARY LOAD
  // ==========================================================================

  useEffect(() => {
    const controller =
      new AbortController();

    loadSummary({
      signal:
        controller.signal,
    });

    return () => {
      controller.abort();
    };
  }, [
    loadSummary,
  ]);


  // ==========================================================================
  // CURRENT PAGE IDS
  // ==========================================================================

  const currentPageIds =
    useMemo(
      () =>
        emails
          .map(
            getEmailId,
          )
          .filter(Boolean),
      [emails],
    );


  // ==========================================================================
  // CURRENT PAGE SELECTION STATE
  // ==========================================================================

  const allCurrentPageSelected =
    currentPageIds.length > 0 &&
    currentPageIds.every(
      (id) =>
        selectedIds.includes(
          id,
        ),
    );


  // ==========================================================================
  // SELECTED EMAIL OBJECTS
  // ==========================================================================

  const selectedEmails =
    useMemo(
      () =>
        emails.filter(
          (email) => {
            const emailId =
              getEmailId(
                email,
              );

            return (
              emailId &&
              selectedIds.includes(
                emailId,
              )
            );
          },
        ),
      [
        emails,
        selectedIds,
      ],
    );


  // ==========================================================================
  // SELECTION COUNT
  // ==========================================================================

  const selectedCount =
    selectedIds.length;


  // ==========================================================================
  // FILTER CHANGE
  // ==========================================================================

  const handleFilterChange =
    useCallback(
      (
        key,
        value,
      ) => {
        if (parsing) {
          return;
        }

        setFilters(
          (current) => ({
            ...current,
            [key]: value,
          }),
        );

        setPage(
          DEFAULT_PAGE,
        );

        setSelectedIds(
          [],
        );

        setAllMatchingSelected(
          false,
        );
      },
      [parsing],
    );


  // ==========================================================================
  // RESET FILTERS
  // ==========================================================================

  const handleResetFilters =
    useCallback(() => {
      if (parsing) {
        return;
      }

      setFilters(
        createEmptyParsingFilters(),
      );

      setPage(
        DEFAULT_PAGE,
      );

      setSelectedIds(
        [],
      );

      setAllMatchingSelected(
        false,
      );
    }, [
      parsing,
    ]);


  // ==========================================================================
  // SELECT CURRENT PAGE
  // ==========================================================================

  const handleSelectAll =
    useCallback(() => {
      if (
        parsing ||
        loading ||
        currentPageIds.length ===
          0
      ) {
        return;
      }

      setSelectedIds(
        (current) => {
          const merged =
            new Set(
              current,
            );

          currentPageIds.forEach(
            (id) =>
              merged.add(id),
          );

          return [
            ...merged,
          ];
        },
      );

      setAllMatchingSelected(
        false,
      );
    }, [
      parsing,
      loading,
      currentPageIds,
    ]);


  // ==========================================================================
  // SELECT ALL MATCHING
  // ==========================================================================

  const handleSelectAllMatching =
    useCallback(
      async () => {
        if (
          parsing ||
          selectionLoading
        ) {
          return;
        }

        setSelectionLoading(
          true,
        );

        setError("");

        try {
          const matchingIds =
            await getMatchingEmailIds({
              filters:
                {
                  ...normalizedFilters,
                  status: "pending",
                },
            });

          const normalizedIds =
            normalizeIdList(
              matchingIds,
            );

          setSelectedIds(
            normalizedIds,
          );

          setAllMatchingSelected(
            normalizedIds.length >
              0,
          );
        } catch (
          requestError
        ) {
          setError(
            getParsingServiceErrorMessage(
              requestError,
            ),
          );

          setSelectedIds(
            [],
          );

          setAllMatchingSelected(
            false,
          );
        } finally {
          setSelectionLoading(
            false,
          );
        }
      },
      [
        parsing,
        selectionLoading,
        normalizedFilters,
      ],
    );


  // ==========================================================================
  // CLEAR SELECTION
  // ==========================================================================

  const handleClearSelection =
    useCallback(() => {
      if (parsing) {
        return;
      }

      setSelectedIds(
        [],
      );

      setAllMatchingSelected(
        false,
      );
    }, [
      parsing,
    ]);


  // ==========================================================================
  // TOGGLE EMAIL SELECTION
  // ==========================================================================

  const handleToggleSelection =
    useCallback(
      (emailId) => {
        if (
          !emailId ||
          parsing
        ) {
          return;
        }

        setSelectedIds(
          (current) => {
            if (
              current.includes(
                emailId,
              )
            ) {
              return current.filter(
                (id) =>
                  id !== emailId,
              );
            }

            return [
              ...current,
              emailId,
            ];
          },
        );

        setAllMatchingSelected(
          false,
        );
      },
      [
        parsing,
      ],
    );


  // ==========================================================================
  // OPEN PARSED EMAIL DRAWER
  // ==========================================================================

  const handleOpenEmail =
    useCallback(
      async (email) => {
        const emailId =
          getEmailId(
            email,
          );

        if (!emailId) {
          return;
        }

        const requestId =
          ++detailRequestId.current;

        setParsedEmailDrawerOpen(
          true,
        );

        setParsedEmailLoading(
          true,
        );

        setParsedEmailError(
          "",
        );

        setParsedEmail(
          null,
        );

        try {
          const response =
            await getParsedEmail(
              emailId,
            );

          if (
            requestId !==
            detailRequestId.current
          ) {
            return;
          }

          setParsedEmail(
            response,
          );
        } catch (
          requestError
        ) {
          if (
            requestId !==
            detailRequestId.current
          ) {
            return;
          }

          setParsedEmailError(
            getParsingServiceErrorMessage(
              requestError,
            ),
          );

          setParsedEmail(
            null,
          );
        } finally {
          if (
            requestId ===
            detailRequestId.current
          ) {
            setParsedEmailLoading(
              false,
            );
          }
        }
      },
      [],
    );


  // ==========================================================================
  // CLOSE PARSED EMAIL DRAWER
  // ==========================================================================

  const handleCloseParsedEmailDrawer =
    useCallback(() => {
      ++detailRequestId.current;

      setParsedEmailDrawerOpen(
        false,
      );

      setParsedEmailLoading(
        false,
      );

      setParsedEmailError(
        "",
      );

      setParsedEmail(
        null,
      );
    }, []);


  // ==========================================================================
  // PARSING QUEUE INITIALIZATION
  // ==========================================================================

  const buildQueueItems =
    useCallback(
      (
        emailsToQueue,
        ids,
      ) => {
        const emailMap =
          new Map(
            emailsToQueue
              .map(
                (email) => [
                  getEmailId(
                    email,
                  ),
                  email,
                ],
              ),
          );

        return ids.map(
          (emailId) => {
            const email =
              emailMap.get(
                emailId,
              );

            return {
              emailId,

              subject:
                email?.subject ||
                "(No subject)",

              sender:
                email?.sender ||
                "Unknown sender",

              status:
                "processing",

              message: "",
            };
          },
        );
      },
      [],
    );


  // ==========================================================================
  // PARSE EXPLICIT IDS
  // ==========================================================================

  const executeBatchParsing =
    useCallback(
      async (
        ids,
        queueItems,
      ) => {
        const normalizedIds =
          normalizeIdList(
            ids,
          );

        if (
          normalizedIds.length ===
          0
        ) {
          return {
            results: [],
            failedIds: [],
          };
        }

        const batches =
          chunkArray(
            normalizedIds,
            BATCH_SIZE,
          );

        const resultMap =
          new Map();

        const failedIds =
          new Set();

        for (
          let index = 0;
          index <
          batches.length;
          index += 1
        ) {
          const batch =
            batches[index];

          try {
            const response =
              await parseEmails(
                batch,
              );

            const results =
              Array.isArray(
                response,
              )
                ? response
                : Array.isArray(
                    response?.results,
                  )
                  ? response.results
                  : [];

            results.forEach(
              (result) => {
                if (
                  result?.email_id
                ) {
                  resultMap.set(
                    result.email_id,
                    result,
                  );
                }
              },
            );

            batch.forEach(
              (emailId) => {
                if (
                  !resultMap.has(
                    emailId,
                  )
                ) {
                  failedIds.add(
                    emailId,
                  );
                }
              },
            );
          } catch (
            batchError
          ) {
            batch.forEach(
              (emailId) => {
                failedIds.add(
                  emailId,
                );
              },
            );

            setQueue(
              (current) =>
                current.map(
                  (item) => {
                    if (
                      !batch.includes(
                        item.emailId,
                      )
                    ) {
                      return item;
                    }

                    return {
                      ...item,

                      status:
                        "failed",

                      message:
                        getParsingServiceErrorMessage(
                          batchError,
                        ),
                    };
                  },
                ),
            );
          }

          const processedCount =
            Math.min(
              (index + 1) *
                BATCH_SIZE,
              normalizedIds.length,
            );

          setQueue(
            (current) =>
              current.map(
                (item) => {
                  if (
                    item.status !==
                    "processing"
                  ) {
                    return item;
                  }

                  return {
                    ...item,

                    message:
                      `Batch progress: ${processedCount}/${normalizedIds.length}`,
                  };
                },
              ),
          );
        }

        setQueue(
          (current) =>
            current.map(
              (item) => {
                const result =
                  resultMap.get(
                    item.emailId,
                  );

                if (!result) {
                  return {
                    ...item,

                    status:
                      "failed",

                    message:
                      failedIds.has(
                        item.emailId,
                      )
                        ? "Parsing failed or no parsing result was returned."
                        : "No parsing result returned for this email.",
                  };
                }

                const parsingStatus =
                  result
                    ?.parsing
                    ?.status ??
                  PARSING_STATUS.FAILED;

                return {
                  ...item,

                  status:
                    getQueueStatus(
                      parsingStatus,
                    ),

                  message:
                    getValidationMessage(
                      result,
                    ),
                };
              },
            ),
        );

        return {
          results: [
            ...resultMap.values(),
          ],

          failedIds: [
            ...failedIds,
          ],
        };
      },
      [],
    );


  // ==========================================================================
  // PARSE SELECTED
  // ==========================================================================

  const handleParseSelected =
    useCallback(
      async () => {
        if (
          selectedIds.length ===
            0 ||
          parsing
        ) {
          return;
        }

        const ids =
          normalizeIdList(
            selectedIds,
          );

        const initialQueue =
          buildQueueItems(
            selectedEmails,
            ids,
          );

        setQueue(
          initialQueue,
        );

        setParsing(
          true,
        );

        setError("");

        try {
          await executeBatchParsing(
            ids,
            initialQueue,
          );

          setSelectedIds(
            [],
          );

          setAllMatchingSelected(
            false,
          );

          await Promise.all([
            loadEmails(),
            loadSummary(),
          ]);
        } catch (
          requestError
        ) {
          setError(
            getParsingServiceErrorMessage(
              requestError,
            ),
          );
        } finally {
          setParsing(
            false,
          );
        }
      },
      [
        selectedIds,
        parsing,
        selectedEmails,
        buildQueueItems,
        executeBatchParsing,
        loadEmails,
        loadSummary,
      ],
    );


  // ==========================================================================
  // PARSE ALL PENDING
  // ==========================================================================

  const handleParseAllPending =
    useCallback(
      async () => {
        if (
          parsing ||
          pendingAllParsing
        ) {
          return;
        }

        try {
          const pendingIds =
            await getPendingEmailIds();

          const normalizedIds =
            normalizeIdList(
              pendingIds,
            );

          if (
            normalizedIds.length ===
            0
          ) {
            setQueue(
              [],
            );

            setSelectedIds(
              [],
            );

            return;
          }

          setPendingAllParsing(true);
          setParsing(true);
          setError("");

          const queueItems =
            buildQueueItems(
              emails,
              normalizedIds,
            );

          setQueue(
            queueItems,
          );

          try {
            const response =
              await parseAllPending({
                confirm: true,
              });

            const results =
              Array.isArray(
                response,
              )
                ? response
                : Array.isArray(
                    response?.results,
                  )
                  ? response.results
                  : [];

            const resultMap =
              new Map(
                results
                  .filter(
                    (result) =>
                      result?.email_id,
                  )
                  .map(
                    (result) => [
                      result.email_id,
                      result,
                    ],
                  ),
              );

            setQueue(
              (current) =>
                current.map(
                  (item) => {
                    const result =
                      resultMap.get(
                        item.emailId,
                      );

                    if (!result) {
                      return {
                        ...item,

                        status:
                          "failed",

                        message:
                          "No parsing result returned for this email.",
                      };
                    }

                    const parsingStatus =
                      result
                        ?.parsing
                        ?.status ??
                      PARSING_STATUS.FAILED;

                    return {
                      ...item,

                      status:
                        getQueueStatus(
                          parsingStatus,
                        ),

                      message:
                        getValidationMessage(
                          result,
                        ),
                    };
                  },
                ),
            );
          } catch (
            batchError
          ) {
            const message =
              getParsingServiceErrorMessage(
                batchError,
              );

            setError(
              message,
            );

            setQueue(
              (current) =>
                current.map(
                  (item) => ({
                    ...item,

                    status:
                      "failed",

                    message,
                  }),
                ),
            );
          }

          setSelectedIds(
            [],
          );

          setAllMatchingSelected(
            false,
          );

          await Promise.all([
            loadEmails(),
            loadSummary(),
          ]);
        } catch (
          requestError
        ) {
          setError(
            getParsingServiceErrorMessage(
              requestError,
            ),
          );
        } finally {
          setPendingAllParsing(
            false,
          );

          setParsing(
            false,
          );
        }
      },
      [
        parsing,
        pendingAllParsing,
        buildQueueItems,
        emails,
        loadEmails,
        loadSummary,
      ],
    );


  // ==========================================================================
  // PAGINATION
  // ==========================================================================

  const totalPages =
    Math.max(
      1,
      pagination.total_pages ||
      1,
    );


  const handlePageChange =
    useCallback(
      (nextPage) => {
        if (
          nextPage < 1 ||
          nextPage >
            totalPages ||
          nextPage === page ||
          parsing
        ) {
          return;
        }

        setPage(
          nextPage,
        );
      },
      [
        page,
        totalPages,
        parsing,
      ],
    );


  // ==========================================================================
  // CURRENT FILTER SUMMARY
  // ==========================================================================

  const activeFilterCount =
    useMemo(() => {
      let count = 0;

      if (
        normalizedFilters.search
      ) {
        count += 1;
      }

      if (
        normalizedFilters.source
      ) {
        count += 1;
      }

      if (
        normalizedFilters.level
      ) {
        count += 1;
      }

      if (
        normalizedFilters.status
      ) {
        count += 1;
      }

      if (
        normalizedFilters.from_date
      ) {
        count += 1;
      }

      if (
        normalizedFilters.to_date
      ) {
        count += 1;
      }

      return count;
    }, [
      normalizedFilters,
    ]);


  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <section
      className="parsing-workspace"
    >

      {/* ================================================================== */}
      {/* HEADER */}
      {/* ================================================================== */}

      <header
        className="parsing-workspace__header"
      >
        <div>
          <h1>
            Email Parsing
          </h1>

          <p>
            Parse, validate and inspect
            collected emails.
          </p>
        </div>
      </header>


      {/* ================================================================== */}
      {/* GLOBAL SUMMARY */}
      {/* ================================================================== */}

      <section
        className="parsing-workspace__summary"
        aria-label="Global parsing summary"
      >
        <div
          className="parsing-workspace__summary-header"
        >
          <div>
            <p
              className="parsing-workspace__eyebrow"
            >
              GLOBAL PARSING SUMMARY
            </p>

            <h2>
              Module 03 Processing State
            </h2>
          </div>

          {summaryLoading && (
            <span
              className="parsing-workspace__summary-loading"
            >
              Updating...
            </span>
          )}
        </div>

        <ParsingStats
          totalCollected={
            summary.total_collected
          }

          totalParsed={
            summary.total_parsed
          }

          totalPending={
            summary.total_pending
          }

          totalWarnings={
            summary.total_warnings
          }

          totalFailed={
            summary.total_failed
          }
        />

        {summaryError && (
          <div
            className="parsing-alert parsing-alert--error"
            role="alert"
          >
            {summaryError}
          </div>
        )}
      </section>


      {/* ================================================================== */}
      {/* FILTERS */}
      {/* ================================================================== */}

      <section
        className="parsing-workspace__filters"
        aria-label="Parsing filters"
      >

        <div
          className="parsing-filter-group"
        >
          <label
            htmlFor="parsing-search"
          >
            Search
          </label>

          <input
            id="parsing-search"
            type="search"
            value={
              filters.search
            }
            placeholder="Subject, sender, Message-ID, source identifier"
            disabled={
              parsing
            }
            onChange={(event) =>
              handleFilterChange(
                "search",
                event.target.value,
              )
            }
          />
        </div>


        <div
          className="parsing-filter-group"
        >
          <label
            htmlFor="parsing-source"
          >
            Source
          </label>

          <select
            id="parsing-source"
            value={
              filters.source
            }
            disabled={
              parsing
            }
            onChange={(event) =>
              handleFilterChange(
                "source",
                event.target.value,
              )
            }
          >
            <option value="">
              All Source
            </option>

            <option value="file_upload">
              File Upload
            </option>

            <option value="raw_email">
              Raw Email
            </option>
          </select>
        </div>


        <div
          className="parsing-filter-group"
        >
          <label
            htmlFor="parsing-level"
          >
            Level
          </label>

          <select
            id="parsing-level"
            value={
              filters.level
            }
            disabled={
              parsing
            }
            onChange={(event) =>
              handleFilterChange(
                "level",
                event.target.value,
              )
            }
          >
            <option value="">
              All Level
            </option>

            <option value="normal">
              Normal
            </option>

            <option value="bombing">
              Bombing
            </option>
          </select>
        </div>


        <div
          className="parsing-filter-group"
        >
          <label
            htmlFor="parsing-status"
          >
            Status
          </label>

          <select
            id="parsing-status"
            value={
              filters.status
            }
            disabled={
              parsing
            }
            onChange={(event) =>
              handleFilterChange(
                "status",
                event.target.value,
              )
            }
          >
            <option value="">
              All Status
            </option>

            <option
              value={
                PARSING_STATUS.PENDING
              }
            >
              Pending
            </option>

            <option
              value={
                PARSING_STATUS.PARSED
              }
            >
              Parsed
            </option>

            <option
              value={
                PARSING_STATUS.WARNING
              }
            >
              Warning
            </option>

            <option
              value={
                PARSING_STATUS.FAILED
              }
            >
              Failed
            </option>
          </select>
        </div>


        <div
          className="parsing-filter-group"
        >
          <label
            htmlFor="parsing-from-date"
          >
            From
          </label>

          <input
            id="parsing-from-date"
            type="date"
            value={
              filters.from_date
            }
            disabled={
              parsing
            }
            onChange={(event) =>
              handleFilterChange(
                "from_date",
                event.target.value,
              )
            }
          />
        </div>


        <div
          className="parsing-filter-group"
        >
          <label
            htmlFor="parsing-to-date"
          >
            To
          </label>

          <input
            id="parsing-to-date"
            type="date"
            value={
              filters.to_date
            }
            disabled={
              parsing
            }
            onChange={(event) =>
              handleFilterChange(
                "to_date",
                event.target.value,
              )
            }
          />
        </div>


        <div
          className="parsing-filter-group parsing-filter-group--reset"
        >
          <button
            type="button"
            className="parsing-button parsing-button--secondary"
            disabled={
              parsing ||
              activeFilterCount ===
                0
            }
            onClick={
              handleResetFilters
            }
          >
            Reset Filters
          </button>
        </div>

      </section>


      {/* ================================================================== */}
      {/* FILTER SUMMARY */}
      {/* ================================================================== */}

      <div
        className="parsing-workspace__filter-summary"
      >
        <span>
          {activeFilterCount > 0
            ? `${activeFilterCount} filter${
                activeFilterCount ===
                1
                  ? ""
                  : "s"
              } active`
            : "All collected emails"}
        </span>
      </div>


      {/* ================================================================== */}
      {/* ACTIONS */}
      {/* ================================================================== */}

      {canManage && <section
        className="parsing-workspace__actions"
      >

        <div
          className="parsing-workspace__selection"
        >
          <strong>
            {selectedCount}
          </strong>

          <span>
            {allMatchingSelected
              ? "matching emails selected"
              : selectedCount === 1
                ? "email selected"
                : "emails selected"}
          </span>
        </div>


        <div
          className="parsing-workspace__action-buttons"
        >

          <button
            type="button"
            className="parsing-button parsing-button--secondary"
            onClick={allMatchingSelected
              ? handleClearSelection
              : handleSelectAllMatching}
            disabled={
              loading ||
              parsing ||
              selectionLoading ||
              pagination.total ===
                0
            }
          >
            {selectionLoading
              ? "Selecting..."
              : allMatchingSelected
                ? "Clear Selection"
                : "Select All Matching"}
          </button>


          <button
            type="button"
            className="parsing-button parsing-button--secondary"
            onClick={
              handleClearSelection
            }
            disabled={
              parsing ||
              selectedCount === 0
            }
          >
            Clear Selection
          </button>


          <button
            type="button"
            className="parsing-button parsing-button--primary"
            onClick={
              handleParseSelected
            }
            disabled={
              parsing ||
              selectedCount === 0
            }
          >
            {parsing &&
            !pendingAllParsing
              ? "Parsing..."
              : `Parse Selected${
                  selectedCount >
                  0
                    ? ` (${selectedCount})`
                    : ""
                }`}
          </button>


          <button
            type="button"
            className="parsing-button parsing-button--danger"
            onClick={
              handleParseAllPending
            }
            disabled={
              parsing ||
              summary.total_pending ===
                0
            }
          >
            {pendingAllParsing
              ? "Parsing Pending..."
              : `Parse All Pending${
                  summary.total_pending >
                  0
                    ? ` (${summary.total_pending})`
                    : ""
                }`}
          </button>

        </div>

      </section>}


      {/* ================================================================== */}
      {/* ERROR */}
      {/* ================================================================== */}

      {error && (
        <div
          className="parsing-alert parsing-alert--error"
          role="alert"
        >
          {error}
        </div>
      )}


      {/* ================================================================== */}
      {/* EMAIL TABLE */}
      {/* ================================================================== */}

      <ParsingEmailTable
        canSelect={canManage}
        emails={
          emails
        }

        selectedIds={
          selectedIds
        }

        loading={
          loading
        }

        allSelected={
          allCurrentPageSelected
        }

        onSelectAll={
          handleSelectAll
        }

        onToggleSelection={
          handleToggleSelection
        }

        onOpenEmail={
          handleOpenEmail
        }
      />


      {/* ================================================================== */}
      {/* PAGINATION */}
      {/* ================================================================== */}

      <div
        className="parsing-pagination"
      >

        <div
          className="parsing-pagination__range"
        >
          {pagination.total >
          0
            ? `${pagination.start_index} - ${pagination.end_index} / Total ${pagination.total}`
            : "No emails found"}
        </div>


        <div
          className="parsing-pagination__controls"
        >

          <button
            type="button"
            className="parsing-button parsing-button--secondary"
            disabled={
              page <= 1 ||
              loading ||
              parsing
            }
            onClick={() =>
              handlePageChange(
                page - 1,
              )
            }
          >
            Previous
          </button>


          <span
            className="parsing-pagination__page"
            aria-current="page"
          >
            Page {page} of{" "}
            {totalPages}
          </span>


          <button
            type="button"
            className="parsing-button parsing-button--secondary"
            disabled={
              page >=
                totalPages ||
              loading ||
              parsing
            }
            onClick={() =>
              handlePageChange(
                page + 1,
              )
            }
          >
            Next
          </button>

        </div>

      </div>


      {/* ================================================================== */}
      {/* PARSING QUEUE */}
      {/* ================================================================== */}

      <ParsingQueue
        items={
          queue
        }

        visible={
          queue.length > 0
        }
      />


      {/* ================================================================== */}
      {/* PARSED EMAIL DETAILS DRAWER */}
      {/* ================================================================== */}

      <ParsedEmailDrawer
        open={
          parsedEmailDrawerOpen
        }

        email={
          parsedEmail
        }

        loading={
          parsedEmailLoading
        }

        error={
          parsedEmailError
        }

        onClose={
          handleCloseParsedEmailDrawer
        }
      />

    </section>
  );
}

/**
 * Module 04 — Feature Engineering
 *
 * Feature Engineering Workspace
 *
 * Layout:
 *
 *   Page Header
 *       ↓
 *   Global Summary
 *       ↓
 *   Filters
 *       ↓
 *   ONE Selection / Action Toolbar
 *       ↓
 *   Feature Workspace
 *       ↓
 *   Table
 *       ↓
 *   Pagination
 *       ↓
 *   Feature Details Drawer
 *
 * IMPORTANT:
 *
 * FeatureTable.jsx is intentionally NOT used here.
 *
 * The workspace owns:
 *   - filtering
 *   - global selection
 *   - current-page selection
 *   - extraction
 *   - pagination
 *   - detail drawer state
 *
 * Feature Engineering responsibilities:
 *
 *   Parsed Email
 *        ↓
 *      F1-F12
 *
 * This page does NOT perform:
 *
 *   Prediction
 *   Confidence
 *   Risk Score
 *   Threat Level
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Eye } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";

import featureService, {
  FeatureApiError,
} from "../services/featureService";

import {
  DEFAULT_PAGE,
  DEFAULT_PAGE_SIZE,

  FEATURE_LEVELS,
  FEATURE_SOURCES,
  FEATURE_STATUS,
  FEATURE_STATUSES,

  createEmptyWorkspaceFilters,
  getFeatureLevelLabel,
  getFeatureSourceLabel,
  getFeatureStatusLabel,
  hasActiveWorkspaceFilters,
  normalizeWorkspaceFilters,
} from "../types";

import FeatureStats from "../components/FeatureStats";

import FeatureDetailsDrawer from "../components/FeatureDetailsDrawer";


// ============================================================================
// CONSTANTS
// ============================================================================

const BATCH_SIZE = 100;


// ============================================================================
// DATE FORMATTER
// ============================================================================

function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return String(value);
  }

  return date.toLocaleString();
}


// ============================================================================
// FEATURE VALUE FORMATTER
// ============================================================================

function formatFeatureValue(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (
    typeof value === "boolean"
  ) {
    return value
      ? "Yes"
      : "No";
  }

  return String(value);
}


// ============================================================================
// STATUS BADGE
// ============================================================================

function FeatureStatusBadge({
  status,
}) {
  const normalized =
    status ||
    FEATURE_STATUS.PENDING;

  return (
    <span
      className={
        "feature-status-badge " +
        `feature-status-badge--${normalized}`
      }
    >
      {getFeatureStatusLabel(
        normalized,
      )}
    </span>
  );
}


// ============================================================================
// LOADING STATE
// ============================================================================

function LoadingState() {
  return (
    <div
      className="feature-workspace__state"
      role="status"
      aria-live="polite"
    >
      Loading feature workspace…
    </div>
  );
}


// ============================================================================
// EMPTY STATE
// ============================================================================

function EmptyState({
  filtered,
}) {
  return (
    <div className="feature-workspace__state">

      <div className="feature-workspace__state-title">
        {filtered
          ? "No matching parsed emails"
          : "No parsed emails found"}
      </div>

      <div className="feature-workspace__state-text">
        {filtered
          ? (
            "No parsed emails match the selected "
            + "Feature Engineering filters."
          )
          : (
            "No successfully parsed emails are "
            + "currently available for Feature Engineering."
          )}
      </div>

    </div>
  );
}


// ============================================================================
// ERROR STATE
// ============================================================================

function ErrorState({
  message,
  onRetry,
}) {
  return (
    <div
      className={
        "feature-workspace__state " +
        "feature-workspace__state--error"
      }
      role="alert"
    >

      <div className="feature-workspace__state-title">
        Unable to load feature workspace
      </div>

      <div className="feature-workspace__state-text">
        {message}
      </div>

      <button
        type="button"
        className={
          "feature-button " +
          "feature-button--secondary"
        }
        onClick={onRetry}
      >
        Retry
      </button>

    </div>
  );
}


// ============================================================================
// OPERATION NOTICE
// ============================================================================

function OperationNotice({
  message,
}) {
  if (!message) {
    return null;
  }

  return (
    <div
      className="feature-workspace__notice"
      role="status"
      aria-live="polite"
    >
      {message}
    </div>
  );
}


// ============================================================================
// FILTER OPTIONS
// ============================================================================

function getSourceOptions() {
  return [
    {
      value: "",
      label: "All Source",
    },

    ...FEATURE_SOURCES.map(
      (source) => ({
        value: source,
        label:
          getFeatureSourceLabel(
            source,
          ),
      }),
    ),
  ];
}


function getLevelOptions() {
  return [
    {
      value: "",
      label: "All Level",
    },

    ...FEATURE_LEVELS.map(
      (level) => ({
        value: level,
        label:
          getFeatureLevelLabel(
            level,
          ),
      }),
    ),
  ];
}


function getStatusOptions() {
  return [
    {
      value: "",
      label: "All Status",
    },

    ...FEATURE_STATUSES.map(
      (status) => ({
        value: status,
        label:
          getFeatureStatusLabel(
            status,
          ),
      }),
    ),
  ];
}


// ============================================================================
// FILTER BAR
// ============================================================================

function FeatureWorkspaceFilters({
  filters,
  onChange,
  onReset,
  disabled,
}) {
  const sourceOptions =
    useMemo(
      () =>
        getSourceOptions(),
      [],
    );

  const levelOptions =
    useMemo(
      () =>
        getLevelOptions(),
      [],
    );

  const statusOptions =
    useMemo(
      () =>
        getStatusOptions(),
      [],
    );

  const updateFilter =
    useCallback(
      (
        field,
        value,
      ) => {
        onChange({
          ...filters,
          [field]: value,
        });
      },
      [
        filters,
        onChange,
      ],
    );

  const filtersActive =
    hasActiveWorkspaceFilters(
      filters,
    );

  return (
    <section
      className="feature-workspace__filters"
      aria-label="Feature workspace filters"
    >

      <div className="feature-filter-grid">

        {/* SEARCH */}

        <div className="feature-filter">

          <label
            htmlFor="feature-filter-search"
            className="feature-filter__label"
          >
            Search
          </label>

          <input
            id="feature-filter-search"
            type="search"
            className="feature-filter__control"
            placeholder={
              "Subject, sender, Message-ID, source identifier"
            }
            value={
              filters.search || ""
            }
            onChange={(event) =>
              updateFilter(
                "search",
                event.target.value,
              )
            }
            disabled={disabled}
            autoComplete="off"
          />

        </div>


        {/* SOURCE */}

        <div className="feature-filter">

          <label
            htmlFor="feature-filter-source"
            className="feature-filter__label"
          >
            Source
          </label>

          <select
            id="feature-filter-source"
            className="feature-filter__control"
            value={
              filters.source || ""
            }
            onChange={(event) =>
              updateFilter(
                "source",
                event.target.value,
              )
            }
            disabled={disabled}
          >
            {sourceOptions.map(
              (option) => (
                <option
                  key={
                    option.value ||
                    "all"
                  }
                  value={
                    option.value
                  }
                >
                  {option.label}
                </option>
              ),
            )}
          </select>

        </div>


        {/* LEVEL */}

        <div className="feature-filter">

          <label
            htmlFor="feature-filter-level"
            className="feature-filter__label"
          >
            Level
          </label>

          <select
            id="feature-filter-level"
            className="feature-filter__control"
            value={
              filters.level || ""
            }
            onChange={(event) =>
              updateFilter(
                "level",
                event.target.value,
              )
            }
            disabled={disabled}
          >
            {levelOptions.map(
              (option) => (
                <option
                  key={
                    option.value ||
                    "all"
                  }
                  value={
                    option.value
                  }
                >
                  {option.label}
                </option>
              ),
            )}
          </select>

        </div>


        {/* STATUS */}

        <div className="feature-filter">

          <label
            htmlFor="feature-filter-status"
            className="feature-filter__label"
          >
            Status
          </label>

          <select
            id="feature-filter-status"
            className="feature-filter__control"
            value={
              filters.status || ""
            }
            onChange={(event) =>
              updateFilter(
                "status",
                event.target.value,
              )
            }
            disabled={disabled}
          >
            {statusOptions.map(
              (option) => (
                <option
                  key={
                    option.value ||
                    "all"
                  }
                  value={
                    option.value
                  }
                >
                  {option.label}
                </option>
              ),
            )}
          </select>

        </div>


        {/* FROM */}

        <div className="feature-filter">

          <label
            htmlFor="feature-filter-from"
            className="feature-filter__label"
          >
            From
          </label>

          <input
            id="feature-filter-from"
            type="date"
            className="feature-filter__control"
            value={
              filters.fromDate || ""
            }
            onChange={(event) =>
              updateFilter(
                "fromDate",
                event.target.value,
              )
            }
            disabled={disabled}
          />

        </div>


        {/* TO */}

        <div className="feature-filter">

          <label
            htmlFor="feature-filter-to"
            className="feature-filter__label"
          >
            To
          </label>

          <input
            id="feature-filter-to"
            type="date"
            className="feature-filter__control"
            value={
              filters.toDate || ""
            }
            onChange={(event) =>
              updateFilter(
                "toDate",
                event.target.value,
              )
            }
            disabled={disabled}
          />

        </div>

      </div>


      {/* RESET */}

      <div className="feature-filter-actions">

        <button
          type="button"
          className={
            "feature-button " +
            "feature-button--secondary"
          }
          onClick={onReset}
          disabled={
            disabled ||
            !filtersActive
          }
        >
          Reset Filters
        </button>

      </div>

    </section>
  );
}


// ============================================================================
// SINGLE ACTION TOOLBAR
// ============================================================================
//
// THIS IS THE ONLY SELECTION / ACTION TOOLBAR.
//
// There is intentionally NO selection toolbar inside the table.
//
// ============================================================================

function FeatureSelectionToolbar({
  selectedCount,
  totalSelectable,

  allMatchingSelected,

  loading,
  selectingAll,
  extracting,
  canManage,

  onSelectAllMatching,
  onClearSelection,
  onExtractSelected,
  onExtractAllPending,
}) {
  return (
    <section
      className="feature-workspace__selection-bar"
    >

      {/* LEFT */}

      <div className="feature-workspace__selection-left">

        <span className="feature-selection-summary">

          <strong>
            {selectedCount}
          </strong>{" "}

          email
          {selectedCount === 1
            ? ""
            : "s"} selected

          {allMatchingSelected &&
            totalSelectable > 0 && (
              <>
                {" "}
                of{" "}
                <strong>
                  {totalSelectable}
                </strong>{" "}
                matching
              </>
            )}

        </span>

      </div>


      {/* RIGHT */}

      <div className="feature-workspace__selection-actions">

        {/* SELECT ALL MATCHING */}

        <button
          type="button"
          className={
            "feature-button " +
            "feature-button--secondary"
          }
          onClick={
            allMatchingSelected
              ? onClearSelection
              : onSelectAllMatching
          }
          disabled={
            loading ||
            selectingAll ||
            extracting
          }
        >
          {selectingAll
            ? "Selecting…"
            : allMatchingSelected
              ? "Clear Selection"
              : "Select All Matching"}
        </button>


        {/* EXTRACT SELECTED */}

        {canManage && <button
          type="button"
          className={
            "feature-button " +
            "feature-button--primary"
          }
          onClick={
            onExtractSelected
          }
          disabled={
            loading ||
            selectingAll ||
            extracting ||
            selectedCount === 0
          }
        >
          {extracting
            ? "Extracting…"
            : "Extract Selected"}
        </button>}


        {/* EXTRACT ALL PENDING */}

        {canManage && <button
          type="button"
          className={
            "feature-button " +
            "feature-button--danger"
          }
          onClick={
            onExtractAllPending
          }
          disabled={
            loading ||
            selectingAll ||
            extracting
          }
        >
          {extracting
            ? "Extracting…"
            : totalSelectable > 0
              ? `Extract All Pending (${totalSelectable})`
              : "Extract All Pending"}
        </button>}

      </div>

    </section>
  );
}


// ============================================================================
// FEATURE TABLE
// ============================================================================
//
// IMPORTANT:
//
// The table contains ONLY the table.
//
// No duplicate selection toolbar.
//
// Action = View
//
// Clicking View opens FeatureDetailsDrawer on the right side.
//
// ============================================================================

function FeatureWorkspaceTable({
  items,
  selectedEmailIds,
  onToggleSelection,
  onToggleCurrentPage,
  allCurrentPageSelected,
  onViewDetails,
  disabled,
  canSelect = true,
}) {
  const selectableItems =
    items.filter(
      (item) =>
        item.parsed === true &&
        item.featureStatus !==
          FEATURE_STATUS.EXTRACTED,
    );

  const selectableCount =
    selectableItems.length;

  return (
    <div className="feature-table-wrapper">

      <table className="feature-table">

        <thead>

          <tr>

            {/* SELECT */}

            {canSelect && <th
              className="feature-table__select-column"
            >
              <input
                type="checkbox"
                aria-label="Select all emails on this page"
                checked={
                  selectableCount > 0 &&
                  allCurrentPageSelected
                }
                onChange={
                  onToggleCurrentPage
                }
                disabled={
                  disabled ||
                  selectableCount === 0
                }
              />
            </th>}


            {/* SUBJECT */}

            <th>
              Subject
            </th>


            {/* SENDER */}

            <th>
              Sender
            </th>


            {/* SOURCE */}

            <th>
              Source
            </th>


            {/* LEVEL */}

            <th>
              Level
            </th>


            {/* RECEIVED */}

            <th>
              Received
            </th>


            {/* STATUS */}

            <th>
              Status
            </th>


            {/* ACTION */}

            <th>
              Action
            </th>

          </tr>

        </thead>


        <tbody>

          {items.map(
            (item) => {

              const emailId =
                item.emailId;

              const selectable =
                item.parsed === true &&
                item.featureStatus !==
                  FEATURE_STATUS.EXTRACTED;

              const selected =
                selectedEmailIds.has(
                  emailId,
                );

              return (
                <tr
                  key={emailId}
                  className={
                    selected
                      ? "feature-table__row--selected"
                      : ""
                  }
                >

                  {/* SELECT */}

                  {canSelect && <td
                    className="feature-table__select-column"
                  >
                    <input
                      type="checkbox"
                      aria-label={
                        `Select ${
                          item.subject ||
                          "email"
                        }`
                      }
                      checked={
                        selected
                      }
                      onChange={() =>
                        onToggleSelection(
                          emailId,
                        )
                      }
                      disabled={
                        disabled ||
                        !selectable
                      }
                    />
                  </td>}


                  {/* SUBJECT */}

                  <td>

                    <div
                      className="feature-table__subject"
                    >
                      <strong>
                        {item.subject ||
                          "(No subject)"}
                      </strong>
                    </div>

                  </td>


                  {/* SENDER */}

                  <td>

                    <div
                      className={
                        "feature-table__sender"
                      }
                    >
                      {item.sender ||
                        "—"}
                    </div>

                  </td>


                  {/* SOURCE */}

                  <td>

                    <div
                      className={
                        "feature-table__source"
                      }
                    >

                      <span>
                        {item.source
                          ? getFeatureSourceLabel(
                              item.source,
                            )
                          : "—"}
                      </span>

                    </div>

                  </td>


                  {/* LEVEL */}

                  <td>

                    {item.level
                      ? getFeatureLevelLabel(
                          item.level,
                        )
                      : "—"}

                  </td>


                  {/* RECEIVED */}

                  <td>

                    {formatDateTime(
                      item.receivedAt,
                    )}

                  </td>


                  {/* STATUS */}

                  <td>

                    <div
                      className={
                        "feature-table__status"
                      }
                    >

                      <FeatureStatusBadge
                        status={
                          item.featureStatus
                        }
                      />

                    </div>

                  </td>


                  {/* ACTION */}

                  <td>

                    <button
                      type="button"
                      className={
                        "feature-table__view-button"
                      }
                      onClick={() =>
                        onViewDetails(
                          emailId,
                        )
                      }
                      disabled={disabled}
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
  );
}


// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function FeatureWorkspace() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);

  // ==========================================================================
  // WORKSPACE DATA
  // ==========================================================================

  const [
    items,
    setItems,
  ] = useState([]);

  const [
    pagination,
    setPagination,
  ] = useState({
    page: DEFAULT_PAGE,
    pageSize: DEFAULT_PAGE_SIZE,
    total: 0,
    totalPages: 0,
    hasPrevious: false,
    hasNext: false,
  });

  const [
    summary,
    setSummary,
  ] = useState({
    totalCollected: 0,
    totalParsed: 0,
    totalFeaturesReady: 0,
    totalPending: 0,
    totalWarnings: 0,
    totalFailed: 0,
    readinessPercentage: 0,
  });


  // ==========================================================================
  // FILTERS
  // ==========================================================================

  const [
    filters,
    setFilters,
  ] = useState(
    createEmptyWorkspaceFilters(),
  );


  // ==========================================================================
  // LOADING
  // ==========================================================================

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    extracting,
    setExtracting,
  ] = useState(false);

  const [
    selectingAll,
    setSelectingAll,
  ] = useState(false);


  // ==========================================================================
  // ERRORS / NOTICES
  // ==========================================================================

  const [
    error,
    setError,
  ] = useState(null);

  const [
    operationMessage,
    setOperationMessage,
  ] = useState(null);


  // ==========================================================================
  // GLOBAL SELECTION
  // ==========================================================================

  /*
   * Contains UUIDs from the complete filtered population.
   *
   * This is NOT limited to the current page.
   */

  const [
    selectedEmailIds,
    setSelectedEmailIds,
  ] = useState(
    new Set(),
  );

  const [
    selectionMeta,
    setSelectionMeta,
  ] = useState({
    totalMatching: 0,
    totalSelectable: 0,
  });


  // ==========================================================================
  // FEATURE DETAILS DRAWER
  // ==========================================================================

  const [
    detailEmailId,
    setDetailEmailId,
  ] = useState(null);

  const [
    detailFeature,
    setDetailFeature,
  ] = useState(null);

  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [
    detailError,
    setDetailError,
  ] = useState(null);


  // ==========================================================================
  // REQUEST GUARDS
  // ==========================================================================

  const workspaceRequestId =
    useRef(0);

  const selectionRequestId =
    useRef(0);

  const detailRequestId =
    useRef(0);


  // ==========================================================================
  // NORMALIZED FILTERS
  // ==========================================================================

  const normalizedFilters =
    useMemo(
      () =>
        normalizeWorkspaceFilters(
          filters,
        ),
      [filters],
    );


  // ==========================================================================
  // LOAD WORKSPACE
  // ==========================================================================

  const loadWorkspace =
    useCallback(
      async ({
        page = DEFAULT_PAGE,
        filtersOverride,
        clearSelection = true,
      } = {}) => {

        const requestId =
          workspaceRequestId.current + 1;

        workspaceRequestId.current =
          requestId;

        setLoading(true);
        setError(null);

        const effectiveFilters =
          normalizeWorkspaceFilters(
            filtersOverride ||
              filters,
          );

        try {

          const [
            workspace,
            workspaceSummary,
          ] = await Promise.all([
            featureService.getFeatures({
              page,

              pageSize:
                pagination.pageSize ||
                DEFAULT_PAGE_SIZE,

              filters:
                effectiveFilters,
            }),

            featureService.getFeatureSummary(),
          ]);


          if (
            requestId !==
            workspaceRequestId.current
          ) {
            return;
          }


          setItems(
            workspace?.items || [],
          );


          setPagination(
            workspace?.pagination || {
              page,
              pageSize:
                DEFAULT_PAGE_SIZE,
              total: 0,
              totalPages: 0,
              hasPrevious: false,
              hasNext: false,
            },
          );


          setSummary(
            workspaceSummary || {},
          );


          if (clearSelection) {

            setSelectedEmailIds(
              new Set(),
            );

            setSelectionMeta({
              totalMatching: 0,
              totalSelectable: 0,
            });

          }

        } catch (err) {

          if (
            requestId !==
            workspaceRequestId.current
          ) {
            return;
          }

          setError(
            err instanceof
              FeatureApiError
              ? err.message
              : (
                "Unable to load Feature Engineering "
                + "workspace."
              ),
          );

        } finally {

          if (
            requestId ===
            workspaceRequestId.current
          ) {
            setLoading(false);
          }

        }

      },
      [
        filters,
        pagination.pageSize,
      ],
    );


  // ==========================================================================
  // INITIAL LOAD
  // ==========================================================================

  useEffect(() => {

    loadWorkspace({
      page: DEFAULT_PAGE,
    });

    // Initial load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, []);


  // ==========================================================================
  // FILTER AUTO REFRESH
  // ==========================================================================

  const previousFiltersRef =
    useRef(
      JSON.stringify(
        createEmptyWorkspaceFilters(),
      ),
    );


  useEffect(() => {

    const serialized =
      JSON.stringify(
        normalizedFilters,
      );


    if (
      previousFiltersRef.current ===
      serialized
    ) {
      return;
    }


    previousFiltersRef.current =
      serialized;


    loadWorkspace({
      page: DEFAULT_PAGE,

      filtersOverride:
        normalizedFilters,

      clearSelection: true,
    });

  }, [
    normalizedFilters,
    loadWorkspace,
  ]);


  // ==========================================================================
  // FILTER CHANGE
  // ==========================================================================

  const handleFiltersChange =
    useCallback(
      (nextFilters) => {

        setFilters(
          normalizeWorkspaceFilters(
            nextFilters,
          ),
        );

        setOperationMessage(
          null,
        );

      },
      [],
    );


  // ==========================================================================
  // RESET FILTERS
  // ==========================================================================

  const resetFilters =
    useCallback(() => {

      const emptyFilters =
        createEmptyWorkspaceFilters();


      previousFiltersRef.current =
        JSON.stringify(
          emptyFilters,
        );


      setFilters(
        emptyFilters,
      );


      setSelectedEmailIds(
        new Set(),
      );


      setSelectionMeta({
        totalMatching: 0,
        totalSelectable: 0,
      });


      setOperationMessage(
        null,
      );


      loadWorkspace({
        page: DEFAULT_PAGE,

        filtersOverride:
          emptyFilters,

        clearSelection: false,
      });

    }, [
      loadWorkspace,
    ]);


  // ==========================================================================
  // CURRENT PAGE SELECTABLE IDS
  // ==========================================================================

  const currentPageSelectableIds =
    useMemo(
      () =>
        items
          .filter(
            (item) =>
              item.parsed === true &&
              item.featureStatus !==
                FEATURE_STATUS.EXTRACTED,
          )
          .map(
            (item) =>
              item.emailId,
          ),
      [items],
    );


  // ==========================================================================
  // CURRENT PAGE SELECTION STATE
  // ==========================================================================

  const allCurrentPageSelected =
    currentPageSelectableIds.length > 0 &&
    currentPageSelectableIds.every(
      (emailId) =>
        selectedEmailIds.has(
          emailId,
        ),
    );


  // ==========================================================================
  // GLOBAL SELECTION STATE
  // ==========================================================================

  const allMatchingSelected =
    selectionMeta.totalSelectable > 0 &&
    selectedEmailIds.size ===
      selectionMeta.totalSelectable;


  // ==========================================================================
  // TOGGLE INDIVIDUAL EMAIL
  // ==========================================================================

  const toggleSelection =
    useCallback(
      (emailId) => {

        if (!emailId) {
          return;
        }


        setSelectedEmailIds(
          (previous) => {

            const next =
              new Set(
                previous,
              );


            if (
              next.has(
                emailId,
              )
            ) {
              next.delete(
                emailId,
              );
            } else {
              next.add(
                emailId,
              );
            }


            return next;
          },
        );

      },
      [],
    );


  // ==========================================================================
  // TOGGLE CURRENT PAGE
  // ==========================================================================

  const toggleCurrentPage =
    useCallback(() => {

      if (
        currentPageSelectableIds.length ===
        0
      ) {
        return;
      }


      if (
        allCurrentPageSelected
      ) {

        setSelectedEmailIds(
          (previous) => {

            const next =
              new Set(
                previous,
              );


            currentPageSelectableIds.forEach(
              (emailId) => {
                next.delete(
                  emailId,
                );
              },
            );


            return next;
          },
        );


        return;
      }


      setSelectedEmailIds(
        (previous) => {

          const next =
            new Set(
              previous,
            );


          currentPageSelectableIds.forEach(
            (emailId) => {
              next.add(
                emailId,
              );
            },
          );


          return next;
        },
      );

    }, [
      currentPageSelectableIds,
      allCurrentPageSelected,
    ]);


  // ==========================================================================
  // SELECT ALL MATCHING
  // ==========================================================================

  const selectAllMatching =
    useCallback(
      async () => {

        if (
          selectingAll ||
          extracting ||
          loading
        ) {
          return;
        }


        const requestId =
          selectionRequestId.current + 1;

        selectionRequestId.current =
          requestId;


        setSelectingAll(
          true,
        );

        setError(null);

        setOperationMessage(
          "Selecting all matching emails…",
        );


        try {

          const response =
            await featureService.getFeatureSelection(
              normalizedFilters,
            );


          if (
            requestId !==
            selectionRequestId.current
          ) {
            return;
          }


          const emailIds =
            Array.isArray(
              response?.emailIds,
            )
              ? response.emailIds
              : [];


          const totalMatching =
            Number(
              response?.totalMatching ??
                0,
            );


          const totalSelectable =
            Number(
              response?.totalSelectable ??
                emailIds.length,
            );


          setSelectedEmailIds(
            new Set(
              emailIds,
            ),
          );


          setSelectionMeta({
            totalMatching,
            totalSelectable,
          });


          if (
            emailIds.length === 0
          ) {

            setOperationMessage(
              "No selectable emails match the current filters.",
            );

          } else {

            setOperationMessage(
              `${emailIds.length} matching selectable `
              + "email(s) selected.",
            );

          }

        } catch (err) {

          if (
            requestId !==
            selectionRequestId.current
          ) {
            return;
          }


          setError(
            err instanceof
              FeatureApiError
              ? err.message
              : (
                "Unable to select all matching emails."
              ),
          );


          setOperationMessage(
            null,
          );

        } finally {

          if (
            requestId ===
            selectionRequestId.current
          ) {
            setSelectingAll(
              false,
            );
          }

        }

      },
      [
        selectingAll,
        extracting,
        loading,
        normalizedFilters,
      ],
    );


  // ==========================================================================
  // CLEAR GLOBAL SELECTION
  // ==========================================================================

  const clearSelection =
    useCallback(() => {

      setSelectedEmailIds(
        new Set(),
      );


      setSelectionMeta({
        totalMatching: 0,
        totalSelectable: 0,
      });


      setOperationMessage(
        null,
      );

    }, []);


  // ==========================================================================
  // EXTRACT SELECTED
  // ==========================================================================

  const handleExtractSelected =
    useCallback(
      async () => {

        const emailIds =
          Array.from(
            selectedEmailIds,
          );


        if (
          emailIds.length === 0
        ) {
          return;
        }


        setExtracting(
          true,
        );

        setError(null);

        setOperationMessage(
          "Starting feature extraction…",
        );


        let processed = 0;
        let extracted = 0;
        let warnings = 0;
        let failed = 0;


        try {

          for (
            let index = 0;
              index < emailIds.length;
              index += BATCH_SIZE
          ) {

            const chunk =
              emailIds.slice(
                index,
                index + BATCH_SIZE,
              );


            const result =
              await featureService.extractFeaturesBatch(
                chunk,
              );


            const resultSummary =
              result?.summary || {};


            processed += Number(
              resultSummary.selected ??
                chunk.length,
            );


            extracted += Number(
              resultSummary.extracted ??
                0,
            );


            warnings += Number(
              resultSummary.warnings ??
                0,
            );


            failed += Number(
              resultSummary.failed ??
                0,
            );


            setOperationMessage(
              `Processing ${Math.min(
                index + BATCH_SIZE,
                emailIds.length,
              )} of ${emailIds.length} selected email(s)…`,
            );

          }


          setSelectedEmailIds(
            new Set(),
          );


          setSelectionMeta({
            totalMatching: 0,
            totalSelectable: 0,
          });


          setOperationMessage(
            `${extracted} of ${processed} email(s) `
            + `processed. ${warnings} warning(s), `
            + `${failed} failed.`,
          );


          await loadWorkspace({
            page:
              pagination.page,

            filtersOverride:
              normalizedFilters,

            clearSelection: false,
          });

        } catch (err) {

          setError(
            err instanceof
              FeatureApiError
              ? err.message
              : "Feature extraction failed.",
          );

        } finally {

          setExtracting(
            false,
          );

        }

      },
      [
        selectedEmailIds,
        loadWorkspace,
        pagination.page,
        normalizedFilters,
      ],
    );


  // ==========================================================================
  // EXTRACT ALL PENDING
  // ==========================================================================

  const handleExtractAllPending =
    useCallback(
      async () => {

        if (
          extracting ||
          selectingAll ||
          loading
        ) {
          return;
        }


        setExtracting(
          true,
        );

        setError(null);

        setOperationMessage(
          "Resolving pending emails…",
        );


        try {

          /*
           * Force:
           *
           *     status = pending
           *
           * while preserving the other active filters.
           */

          const pendingFilters =
            normalizeWorkspaceFilters({
              ...normalizedFilters,

              status:
                FEATURE_STATUS.PENDING,
            });


          const response =
            await featureService.getFeatureSelection(
              pendingFilters,
            );


          const pendingIds =
            Array.isArray(
              response?.emailIds,
            )
              ? response.emailIds
              : [];


          if (
            pendingIds.length === 0
          ) {

            setOperationMessage(
              "No pending emails match the current filters.",
            );

            return;
          }


          let processed = 0;
          let extracted = 0;
          let warnings = 0;
          let failed = 0;


          for (
            let index = 0;
              index < pendingIds.length;
              index += BATCH_SIZE
          ) {

            const chunk =
              pendingIds.slice(
                index,
                index + BATCH_SIZE,
              );


            const result =
              await featureService.extractFeaturesBatch(
                chunk,
              );


            const resultSummary =
              result?.summary || {};


            processed += Number(
              resultSummary.selected ??
                chunk.length,
            );


            extracted += Number(
              resultSummary.extracted ??
                0,
            );


            warnings += Number(
              resultSummary.warnings ??
                0,
            );


            failed += Number(
              resultSummary.failed ??
                0,
            );


            setOperationMessage(
              `Processing ${Math.min(
                index + BATCH_SIZE,
                pendingIds.length,
              )} of ${pendingIds.length} pending email(s)…`,
            );

          }


          setSelectedEmailIds(
            new Set(),
          );


          setSelectionMeta({
            totalMatching: 0,
            totalSelectable: 0,
          });


          setOperationMessage(
            `${extracted} of ${processed} pending `
            + `email(s) processed. `
            + `${warnings} warning(s), `
            + `${failed} failed.`,
          );


          await loadWorkspace({
            page:
              pagination.page,

            filtersOverride:
              normalizedFilters,

            clearSelection: false,
          });

        } catch (err) {

          setError(
            err instanceof
              FeatureApiError
              ? err.message
              : (
                "Pending feature extraction failed."
              ),
          );

        } finally {

          setExtracting(
            false,
          );

        }

      },
      [
        extracting,
        selectingAll,
        loading,
        normalizedFilters,
        loadWorkspace,
        pagination.page,
      ],
    );


  // ==========================================================================
  // REFRESH
  // ==========================================================================

  const handleRefresh =
    useCallback(() => {

      setOperationMessage(
        null,
      );


      loadWorkspace({
        page:
          pagination.page,

        filtersOverride:
          normalizedFilters,

        clearSelection: true,
      });

    }, [
      loadWorkspace,
      pagination.page,
      normalizedFilters,
    ]);


  // ==========================================================================
  // OPEN FEATURE DETAILS DRAWER
  // ==========================================================================

  const openFeatureDetails =
    useCallback(
      async (emailId) => {

        if (!emailId) {
          return;
        }


        const requestId =
          detailRequestId.current + 1;

        detailRequestId.current =
          requestId;


        /*
         * Open the drawer immediately.
         *
         * The drawer shows its own loading state
         * while the feature record is being fetched.
         */

        setDetailEmailId(
          emailId,
        );


        setDetailFeature(
          null,
        );


        setDetailError(
          null,
        );


        setDetailLoading(
          true,
        );


        try {

          const feature =
            await featureService.getFeatureDetailsForDrawer(
              emailId,
            );


          if (
            requestId !==
            detailRequestId.current
          ) {
            return;
          }


          setDetailFeature(
            feature,
          );

        } catch (err) {

          if (
            requestId !==
            detailRequestId.current
          ) {
            return;
          }


          setDetailError(
            err instanceof
              FeatureApiError
              ? err.message
              : (
                "Unable to load feature details."
              ),
          );

        } finally {

          if (
            requestId ===
            detailRequestId.current
          ) {
            setDetailLoading(
              false,
            );
          }

        }

      },
      [],
    );


  // ==========================================================================
  // CLOSE FEATURE DETAILS DRAWER
  // ==========================================================================

  const closeFeatureDetails =
    useCallback(() => {

      detailRequestId.current += 1;


      setDetailEmailId(
        null,
      );


      setDetailFeature(
        null,
      );


      setDetailError(
        null,
      );


      setDetailLoading(
        false,
      );

    }, []);


  // ==========================================================================
  // PAGINATION
  // ==========================================================================

  const handlePreviousPage =
    useCallback(() => {

      if (
        !pagination.hasPrevious ||
        loading ||
        extracting ||
        selectingAll
      ) {
        return;
      }


      loadWorkspace({
        page:
          pagination.page - 1,

        filtersOverride:
          normalizedFilters,

        /*
         * IMPORTANT:
         *
         * Keep global selection while moving
         * between pages.
         */

        clearSelection: false,
      });

    }, [
      pagination.hasPrevious,
      pagination.page,
      loading,
      extracting,
      selectingAll,
      loadWorkspace,
      normalizedFilters,
    ]);


  const handleNextPage =
    useCallback(() => {

      if (
        !pagination.hasNext ||
        loading ||
        extracting ||
        selectingAll
      ) {
        return;
      }


      loadWorkspace({
        page:
          pagination.page + 1,

        filtersOverride:
          normalizedFilters,

        /*
         * IMPORTANT:
         *
         * Keep global selection while moving
         * between pages.
         */

        clearSelection: false,
      });

    }, [
      pagination.hasNext,
      pagination.page,
      loading,
      extracting,
      selectingAll,
      loadWorkspace,
      normalizedFilters,
    ]);


  // ==========================================================================
  // EMPTY STATE
  // ==========================================================================

  const showEmptyState =
    !loading &&
    !error &&
    items.length === 0;


  // ==========================================================================
  // RENDER
  // ==========================================================================

  return (
    <main className="feature-workspace">

      {/* ================================================================== */}
      {/* PAGE HEADER                                                        */}
      {/* ================================================================== */}

      <header className="feature-workspace__header">

        <div>

          <h1 className="feature-workspace__title">
            Feature Engineering
          </h1>

          <p className="feature-workspace__subtitle">
            Extract and inspect structured security
            features from parsed emails.
          </p>

        </div>


        <button
          type="button"
          className={
            "feature-button " +
            "feature-button--secondary"
          }
          onClick={
            handleRefresh
          }
          disabled={
            loading ||
            extracting ||
            selectingAll
          }
        >
          Refresh
        </button>

      </header>


      {/* ================================================================== */}
      {/* GLOBAL SUMMARY                                                     */}
      {/* ================================================================== */}

      <FeatureStats
        summary={
          summary
        }
        loading={
          loading
        }
      />


      {/* ================================================================== */}
      {/* FILTERS                                                            */}
      {/* ================================================================== */}

      <FeatureWorkspaceFilters
        filters={
          filters
        }
        onChange={
          handleFiltersChange
        }
        onReset={
          resetFilters
        }
        disabled={
          loading ||
          extracting ||
          selectingAll
        }
      />


      {/* ================================================================== */}
      {/* OPERATION NOTICE                                                   */}
      {/* ================================================================== */}

      <OperationNotice
        message={
          operationMessage
        }
      />


      {/* ================================================================== */}
      {/* ERROR                                                              */}
      {/* ================================================================== */}

      {error && (
        <ErrorState
          message={
            error
          }
          onRetry={
            handleRefresh
          }
        />
      )}


      {/* ================================================================== */}
      {/* SINGLE SELECTION / ACTION TOOLBAR                                  */}
      {/* ================================================================== */}

      {!error && canManage && (
        <FeatureSelectionToolbar
          canManage={canManage}
          selectedCount={
            selectedEmailIds.size
          }

          totalSelectable={
            selectionMeta.totalSelectable
          }

          allMatchingSelected={
            allMatchingSelected
          }

          loading={
            loading
          }

          selectingAll={
            selectingAll
          }

          extracting={
            extracting
          }

          onSelectAllMatching={
            selectAllMatching
          }

          onClearSelection={
            clearSelection
          }

          onExtractSelected={
            handleExtractSelected
          }

          onExtractAllPending={
            handleExtractAllPending
          }
        />
      )}


      {/* ================================================================== */}
      {/* FEATURE WORKSPACE                                                  */}
      {/* ================================================================== */}

      <section
        className={
          "feature-workspace__table-section"
        }
      >

        <div className="feature-section-heading">

          <div>

            <h2>
              Feature Workspace
            </h2>

            <p>
              {pagination.total} parsed email
              {pagination.total === 1
                ? ""
                : "s"}{" "}
              available
            </p>

          </div>

        </div>


        {loading ? (

          <LoadingState />

        ) : showEmptyState ? (

          <EmptyState
            filtered={
              hasActiveWorkspaceFilters(
                filters,
              )
            }
          />

        ) : (

          <FeatureWorkspaceTable
            canSelect={canManage}

            items={
              items
            }

            selectedEmailIds={
              selectedEmailIds
            }

            onToggleSelection={
              toggleSelection
            }

            onToggleCurrentPage={
              toggleCurrentPage
            }

            allCurrentPageSelected={
              allCurrentPageSelected
            }

            onViewDetails={
              openFeatureDetails
            }

            disabled={
              extracting ||
              selectingAll
            }

          />

        )}

      </section>


      {/* ================================================================== */}
      {/* PAGINATION                                                         */}
      {/* ================================================================== */}

      {!loading &&
        !error &&
        pagination.totalPages > 0 && (

          <nav
            className="feature-pagination"
            aria-label="Feature email pagination"
          >

            <div className="feature-pagination__info">
              <span className="feature-pagination__range">
                {pagination.total > 0
                  ? `${Math.min((pagination.page - 1) * pagination.pageSize + 1, pagination.total)} - ${Math.min(pagination.page * pagination.pageSize, pagination.total)} / Total ${pagination.total}`
                  : "No emails found"}
              </span>
            </div>

            <div className="feature-pagination__controls">
              <button
                type="button"
                className={
                  "feature-button " +
                  "feature-button--secondary"
                }
                onClick={handlePreviousPage}
                disabled={
                  !pagination.hasPrevious ||
                  loading ||
                  extracting ||
                  selectingAll
                }
                aria-label="Go to previous page"
              >
                Previous
              </button>

              <span className="feature-pagination__page">
                Page <strong>{pagination.page}</strong> of{" "}
                <strong>{pagination.totalPages}</strong>
              </span>

              <button
                type="button"
                className={
                  "feature-button " +
                  "feature-button--secondary"
                }
                onClick={handleNextPage}
                disabled={
                  !pagination.hasNext ||
                  loading ||
                  extracting ||
                  selectingAll
                }
                aria-label="Go to next page"
              >
                Next
              </button>
            </div>

          </nav>

        )}


      {/* ================================================================== */}
      {/* FEATURE DETAILS DRAWER                                             */}
      {/* ================================================================== */}
      {/*
       * IMPORTANT:
       *
       * Details are NOT rendered below the table.
       *
       * Clicking "View" opens the dedicated right-side
       * FeatureDetailsDrawer component.
       */}

      <FeatureDetailsDrawer
        open={
          Boolean(
            detailEmailId,
          )
        }

        feature={
          detailFeature
        }

        loading={
          detailLoading
        }

        error={
          detailError
        }

        onClose={
          closeFeatureDetails
        }
      />

    </main>
  );
}

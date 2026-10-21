import {
  useCallback,
  useEffect,
  useState,
} from "react";

import EmailStats from "../components/EmailStats";
import EmailTable from "../components/EmailTable";
import EmailDrawer from "../components/EmailDrawer";

import emailService from "../services/emailService";
import { useAuth } from "../../../core/auth/AuthProvider";
import { PERMISSIONS, hasPermission } from "../../../core/permissions/permissions";

import {
  EMAIL_GROUND_TRUTH_OPTIONS,
  EMAIL_SOURCE_OPTIONS,
} from "../types";


const PAGE_SIZE = 30;


const INITIAL_EMAIL_DATA = {
  items: [],
  total: 0,
  page: 1,
  page_size: PAGE_SIZE,
  total_pages: 1,
  start_index: 0,
  end_index: 0,
  has_previous: false,
  has_next: false,
};


const INITIAL_STATS = {
  total_emails: 0,
  normal_emails: 0,
  bombing_emails: 0,
};


const INITIAL_FILTERS = {
  search: "",
  source: "",
  status: "",
  fromDate: "",
  toDate: "",
};


// ============================================================
// EMAIL OVERVIEW
// ============================================================

export default function EmailOverview() {
  const { user } = useAuth();
  const canIngest = hasPermission(user, PERMISSIONS.EMAILS_INGEST);
  // ==========================================================
  // STATE
  // ==========================================================

  const [emailData, setEmailData] =
    useState(INITIAL_EMAIL_DATA);

  const [stats, setStats] =
    useState(INITIAL_STATS);

  const [filters, setFilters] =
    useState(INITIAL_FILTERS);

  const [currentPage, setCurrentPage] =
    useState(1);

  const [loading, setLoading] =
    useState(true);

  const [statsLoading, setStatsLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [statsError, setStatsError] =
    useState("");

  // Drawer state.
  const [drawerMode, setDrawerMode] =
    useState(null);

  // This must contain the FULL detail response
  // when the drawer is opened in VIEW mode.
  const [selectedEmail, setSelectedEmail] =
    useState(null);

  const [drawerLoading, setDrawerLoading] =
    useState(false);


  // ==========================================================
  // LOAD EMAIL LIST
  // ==========================================================

  const loadEmails = useCallback(
    async (
      requestedPage = 1,
      activeFilters = INITIAL_FILTERS,
    ) => {
      setLoading(true);
      setError("");

      try {
        const response =
          await emailService.listEmails({
            page: requestedPage,
            pageSize: PAGE_SIZE,
            search: activeFilters.search,
            source: activeFilters.source,
            status: activeFilters.status,
            fromDate: activeFilters.fromDate,
            toDate: activeFilters.toDate,
          });

        setEmailData(
          response || INITIAL_EMAIL_DATA,
        );

        setCurrentPage(
          response?.page ??
            requestedPage,
        );
      } catch (requestError) {
        setError(
          requestError?.message ||
            "Unable to load emails.",
        );
      } finally {
        setLoading(false);
      }
    },
    [],
  );


  // ==========================================================
  // LOAD STATISTICS
  // ==========================================================

  const loadStatistics =
    useCallback(async () => {
      setStatsLoading(true);
      setStatsError("");

      try {
        const response =
          await emailService.getEmailStatistics();

        setStats(
          response || INITIAL_STATS,
        );
      } catch (requestError) {
        setStatsError(
          requestError?.message ||
            "Unable to load email statistics.",
        );
      } finally {
        setStatsLoading(false);
      }
    }, []);


  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {
    loadEmails(
      1,
      INITIAL_FILTERS,
    );

    loadStatistics();
  }, [
    loadEmails,
    loadStatistics,
  ]);


  // ==========================================================
  // FILTER UPDATE
  // ==========================================================

  const updateFilter = useCallback(
    (name, value) => {
      const nextFilters = {
        ...filters,
        [name]: value,
      };

      setFilters(nextFilters);
      setCurrentPage(1);

      loadEmails(
        1,
        nextFilters,
      );
    },
    [
      filters,
      loadEmails,
    ],
  );


  // ==========================================================
  // RESET FILTERS
  // ==========================================================

  const resetFilters =
    useCallback(() => {
      setFilters(
        INITIAL_FILTERS,
      );

      setCurrentPage(1);

      loadEmails(
        1,
        INITIAL_FILTERS,
      );
    }, [loadEmails]);


  // ==========================================================
  // PAGINATION DATA
  // ==========================================================

  const totalPages =
    emailData?.total_pages ?? 1;

  const hasPrevious =
    emailData?.has_previous ??
    currentPage > 1;

  const hasNext =
    emailData?.has_next ??
    currentPage < totalPages;

  const startIndex =
    emailData?.start_index ?? 0;

  const endIndex =
    emailData?.end_index ?? 0;

  const totalEmails =
    emailData?.total ?? 0;


  // ==========================================================
  // PREVIOUS PAGE
  // ==========================================================

  const goToPreviousPage =
    useCallback(() => {
      if (
        loading ||
        !hasPrevious
      ) {
        return;
      }

      const previousPage =
        Math.max(
          1,
          currentPage - 1,
        );

      setCurrentPage(
        previousPage,
      );

      loadEmails(
        previousPage,
        filters,
      );
    }, [
      currentPage,
      filters,
      hasPrevious,
      loadEmails,
      loading,
    ]);


  // ==========================================================
  // NEXT PAGE
  // ==========================================================

  const goToNextPage =
    useCallback(() => {
      if (
        loading ||
        !hasNext
      ) {
        return;
      }

      const nextPage =
        Math.min(
          totalPages,
          currentPage + 1,
        );

      setCurrentPage(
        nextPage,
      );

      loadEmails(
        nextPage,
        filters,
      );
    }, [
      currentPage,
      filters,
      hasNext,
      loadEmails,
      loading,
      totalPages,
    ]);


  // ==========================================================
  // OPEN ADD DRAWER
  // ==========================================================

  const openAddDrawer =
    useCallback(() => {
      setSelectedEmail(null);
      setDrawerLoading(false);
      setDrawerMode("add");
    }, []);


  // ==========================================================
  // OPEN VIEW DRAWER
  // ==========================================================
  //
  // IMPORTANT:
  //
  // Do NOT pass the list item directly to EmailDrawer.
  //
  // The list response is intentionally lightweight.
  // We must request the full detail response using email.id.
  //
  // Flow:
  //
  // EmailTable
  //     ↓
  // email.id
  //     ↓
  // emailService.getEmail(id)
  //     ↓
  // EmailDetailResponse
  //     ↓
  // EmailDrawer
  //
  // ==========================================================

  const openViewDrawer =
    useCallback(async (email) => {
      if (!email?.id) {
        return;
      }

      setDrawerMode("view");
      setSelectedEmail(null);
      setDrawerLoading(true);

      try {
        const detail =
          await emailService.getEmail(
            email.id,
          );

        setSelectedEmail(
          detail || null,
        );
      } catch (requestError) {
        console.error(
          "Failed to load email details:",
          requestError,
        );

        setSelectedEmail({
          ...email,
          __detailError:
            requestError?.message ||
            "Unable to load email details.",
        });
      } finally {
        setDrawerLoading(false);
      }
    }, []);


  // ==========================================================
  // CLOSE DRAWER
  // ==========================================================

  const closeDrawer =
    useCallback(() => {
      setDrawerMode(null);
      setSelectedEmail(null);
      setDrawerLoading(false);
    }, []);


  // ==========================================================
  // AFTER EMAIL INGESTION
  // ==========================================================

  const handleEmailAdded =
    useCallback(async (result) => {
      // Keep the upload drawer open when the backend reports partial
      // failures so the remaining files can be reviewed or retried.
      if (!(result?.failed > 0)) {
        closeDrawer();
      }

      await Promise.all([
        loadEmails(
          1,
          filters,
        ),
        loadStatistics(),
      ]);

      setCurrentPage(1);
    }, [
      closeDrawer,
      filters,
      loadEmails,
      loadStatistics,
    ]);


  // ==========================================================
  // RETRY EMAIL LIST
  // ==========================================================

  const handleRetry =
    useCallback(() => {
      loadEmails(
        currentPage,
        filters,
      );
    }, [
      currentPage,
      filters,
      loadEmails,
    ]);


  // ==========================================================
  // RETRY STATISTICS
  // ==========================================================

  const handleStatsRetry =
    useCallback(() => {
      loadStatistics();
    }, [
      loadStatistics,
    ]);


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="email-page">

      {/* ======================================================
          PAGE HEADER
      ======================================================= */}

      <header className="email-page-header">
        <div>
          <span className="email-page-eyebrow">
            EMAIL SECURITY
          </span>

          <h1>
            Email Management
          </h1>

          <p>
            Manage collected emails and
            ground-truth labels.
          </p>
        </div>

        {canIngest && <div className="email-page-header-actions">
          <button
            type="button"
            className="email-primary-button"
            onClick={openAddDrawer}
          >
            + Add Emails
          </button>
        </div>}
      </header>


      {/* ======================================================
          STATISTICS ERROR
      ======================================================= */}

      {statsError && (
        <div
          className="email-form-alert email-form-alert-error"
          role="alert"
        >
          <strong>
            Unable to load statistics
          </strong>

          <span>
            {statsError}
          </span>

          <button
            type="button"
            className="email-secondary-button"
            onClick={handleStatsRetry}
          >
            Try Again
          </button>
        </div>
      )}


      {/* ======================================================
          STATISTICS
      ======================================================= */}

      <EmailStats
        stats={
          statsLoading
            ? INITIAL_STATS
            : stats
        }
      />


      {/* ======================================================
          EMAIL MANAGEMENT
      ======================================================= */}

      <section className="email-page-section">

        {/* ====================================================
            SECTION HEADER
        ===================================================== */}

        <div className="email-section-header">
          <div>
            <span className="email-section-eyebrow">
              EMAILS
            </span>

            <h2>
              Email Management
            </h2>

            <p>
              Search, filter, and review
              collected emails.
            </p>
          </div>
        </div>


        {/* ====================================================
            FILTERS
        ===================================================== */}

        <div className="email-filters">

          {/* SEARCH */}

          <div className="email-filter-field email-filter-search">
            <label htmlFor="email-search">
              Search
            </label>

            <input
              id="email-search"
              type="text"
              value={filters.search}
              onChange={(event) =>
                updateFilter(
                  "search",
                  event.target.value,
                )
              }
              placeholder="Subject, sender, recipient..."
            />
          </div>


          {/* SOURCE */}

          <div className="email-filter-field">
            <label htmlFor="email-source">
              Source
            </label>

            <select
              id="email-source"
              value={filters.source}
              onChange={(event) =>
                updateFilter(
                  "source",
                  event.target.value,
                )
              }
            >
              <option value="">
                All Sources
              </option>

              {EMAIL_SOURCE_OPTIONS.map(
                (option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ),
              )}
            </select>
          </div>


          {/* STATUS */}

          <div className="email-filter-field">
            <label htmlFor="email-status">
              Status
            </label>

            <select
              id="email-status"
              value={filters.status}
              onChange={(event) =>
                updateFilter(
                  "status",
                  event.target.value,
                )
              }
            >
              <option value="">
                All Statuses
              </option>

              {EMAIL_GROUND_TRUTH_OPTIONS.map(
                (option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ),
              )}
            </select>
          </div>


          {/* FROM */}

          <div className="email-filter-field">
            <label htmlFor="email-from-date">
              From
            </label>

            <input
              id="email-from-date"
              type="date"
              value={filters.fromDate}
              onChange={(event) =>
                updateFilter(
                  "fromDate",
                  event.target.value,
                )
              }
            />
          </div>


          {/* TO */}

          <div className="email-filter-field">
            <label htmlFor="email-to-date">
              To
            </label>

            <input
              id="email-to-date"
              type="date"
              value={filters.toDate}
              onChange={(event) =>
                updateFilter(
                  "toDate",
                  event.target.value,
                )
              }
            />
          </div>

        </div>


        {/* ====================================================
            RESET FILTERS
        ===================================================== */}

        <div className="email-filter-actions">
          <button
            type="button"
            className="email-secondary-button"
            onClick={resetFilters}
            disabled={
              !filters.search &&
              !filters.source &&
              !filters.status &&
              !filters.fromDate &&
              !filters.toDate
            }
          >
            Reset Filters
          </button>
        </div>


        {/* ====================================================
            EMAIL LIST ERROR
        ===================================================== */}

        {error && (
          <div
            className="email-form-alert email-form-alert-error"
            role="alert"
          >
            <strong>
              Unable to load emails
            </strong>

            <span>
              {error}
            </span>

            <button
              type="button"
              className="email-secondary-button"
              onClick={handleRetry}
            >
              Try Again
            </button>
          </div>
        )}


        {/* ====================================================
            EMAIL TABLE
        ===================================================== */}

        <EmailTable
          emails={
            emailData?.items ?? []
          }
          loading={loading}
          error={error}
          onRetry={handleRetry}
          onView={openViewDrawer}
          emptyMessage={
            Object.values(
              filters,
            ).some(Boolean)
              ? "No emails match the selected filters."
              : "No emails have been added yet."
          }
        />


        {/* ====================================================
            PAGINATION
        ===================================================== */}

        {!loading &&
          !error &&
          totalEmails > 0 && (
            <div
              className="email-pagination"
              aria-label="Email pagination"
            >
              <div className="email-pagination-summary">
                <span>
                  {startIndex} - {endIndex}
                </span>

                <span>
                  / Total {totalEmails}
                </span>
              </div>

              <div className="email-pagination-controls">
                <button
                  type="button"
                  className="email-pagination-button"
                  onClick={
                    goToPreviousPage
                  }
                  disabled={
                    !hasPrevious ||
                    loading
                  }
                  aria-label="Go to previous page"
                >
                  <span aria-hidden="true">
                    ‹
                  </span>

                  Previous
                </button>

                <span className="email-pagination-page">
                  Page{" "}
                  <strong>
                    {currentPage}
                  </strong>{" "}
                  of{" "}
                  <strong>
                    {totalPages}
                  </strong>
                </span>

                <button
                  type="button"
                  className="email-pagination-button"
                  onClick={
                    goToNextPage
                  }
                  disabled={
                    !hasNext ||
                    loading
                  }
                  aria-label="Go to next page"
                >
                  Next

                  <span aria-hidden="true">
                    ›
                  </span>
                </button>
              </div>
            </div>
          )}


        {!loading &&
          !error &&
          totalEmails === 0 && (
            <div className="email-pagination email-pagination-empty">
              <span>
                No emails available.
              </span>
            </div>
          )}

      </section>


      {/* ======================================================
          ADD / VIEW DRAWER
      ======================================================= */}

      {drawerMode && (
        <EmailDrawer
          mode={drawerMode}
          email={selectedEmail}
          loading={drawerLoading}
          onClose={closeDrawer}
          onSuccess={handleEmailAdded}
        />
      )}

    </div>
  );
}

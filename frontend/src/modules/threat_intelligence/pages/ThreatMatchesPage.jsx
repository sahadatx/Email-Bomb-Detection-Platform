import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import { apiRequest } from "../../../core/api/client";
import ThreatPageHeader from "../components/ThreatPageHeader";
import ThreatFilters from "../components/ThreatFilters";
import ThreatSummaryCards from "../components/ThreatSummaryCards";
import ThreatDrawer from "../components/ThreatDrawer";
import ThreatDrawerContent from "../components/ThreatDrawerContent";
import ThreatMatchTable from "../components/ThreatMatchTable";
import ThreatMatchDetails from "../components/ThreatMatchDetails";
import ThreatRelatedRecord from "../components/ThreatRelatedRecord";
import useThreatFilters from "../hooks/useThreatFilters";
import useThreatMatches from "../hooks/useThreatMatches";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage, displayLabel } from "../types/threatIntelligence";
import "../styles/threatIntelligence.css";

const DEFAULTS = {
  search: "",
  time_range: "30d",
  from_date: "",
  to_date: "",
  classification: "",
  severity: "",
  indicator_type: "",
  feed_id: "",
  status: "",
  page: 1,
  page_size: 30,
};

function ThreatMatchFilters({ fields, filters, update, reset }) {
  return (
    <ThreatFilters
      fields={fields}
      values={filters}
      onChange={update}
      onReset={reset}
    >
      <>
        <label>
          From
          <input
            type="date"
            value={filters.from_date}
            max={filters.to_date || undefined}
            onChange={(event) => {
              update("time_range", "custom");
              update("from_date", event.target.value);
            }}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={filters.to_date}
            min={filters.from_date || undefined}
            onChange={(event) => {
              update("time_range", "custom");
              update("to_date", event.target.value);
            }}
          />
        </label>
      </>
    </ThreatFilters>
  );
}

export default function ThreatMatchesPage() {
  const { user } = useAuth();
  const canInvestigate = ["ADMIN", "SECURITY_ANALYST"].includes(
    user?.role,
  );
  const { filters, query, update, reset } = useThreatFilters(DEFAULTS);
  const params = useMemo(
    () =>
      filters.time_range === "custom"
        ? !filters.from_date || !filters.to_date
          ? null
          : {
              ...query,
              from_date: `${filters.from_date}T00:00:00Z`,
              to_date: `${filters.to_date}T23:59:59Z`,
            }
        : query,
    [filters, query],
  );
  const { data, summary, loading, error, refresh } = useThreatMatches(
    params || {},
  );
  const [feeds, setFeeds] = useState([]);
  const [drawerMatch, setDrawerMatch] = useState(null);
  const [record, setRecord] = useState(null);
  const [stack, setStack] = useState([]);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState("");
  const [reconciling, setReconciling] = useState(false);
  const [reconcileMessage, setReconcileMessage] = useState("");
  const [reconcileError, setReconcileError] = useState("");
  useEffect(() => {
    threatIntelligenceService
      .feeds({ page: 1, page_size: 100, sync_status: "success" })
      .then((value) => setFeeds(value.items || []))
      .catch(() => {});
  }, []);
  const fields = [
    {
      key: "search",
      label: "Search",
      type: "search",
      placeholder: "Search email ID or indicator...",
    },
    {
      key: "classification",
      label: "Classification",
      allLabel: "All classifications",
      options: ["normal", "bomb", "unknown"],
    },
    {
      key: "severity",
      label: "Severity",
      kind: "severity",
      allLabel: "All severities",
    },
    {
      key: "indicator_type",
      label: "Indicator Type",
      kind: "type",
      allLabel: "All types",
    },
    {
      key: "feed_id",
      label: "Feed",
      allLabel: "All feeds",
      options: feeds.map((feed) => ({ value: feed.id, label: feed.name })),
    },
    {
      key: "status",
      label: "Match Status",
      kind: "status",
      allLabel: "All statuses",
    },
  ];
  async function view(match) {
    setDrawerMatch(match);
    setRecord(match);
    setStack([]);
    setDrawerError("");
    setDrawerLoading(true);
    try {
      const result = await threatIntelligenceService.match(match.id);
      setDrawerMatch(result);
      setRecord(result);
    } catch (cause) {
      setDrawerError(errorMessage(cause));
    } finally {
      setDrawerLoading(false);
    }
  }
  async function related(kind, id) {
    if (!id) return;
    setStack((current) => [...current, { kind: "match", data: drawerMatch }]);
    setDrawerLoading(true);
    setDrawerError("");
    try {
      const path =
        kind === "email"
          ? `/emails/${encodeURIComponent(id)}`
          : kind === "detection"
            ? `/detection/${encodeURIComponent(id)}`
            : null;
      const result =
        kind === "indicator"
          ? await threatIntelligenceService.indicator(id)
          : await apiRequest(path);
      setRecord({ kind, data: result });
    } catch (cause) {
      setDrawerError(errorMessage(cause));
      setRecord({ kind, id });
    } finally {
      setDrawerLoading(false);
    }
  }
  async function setStatus(value) {
    if (!drawerMatch) return;
    setDrawerError("");
    try {
      const updated = await threatIntelligenceService.updateMatchStatus(
        drawerMatch.id,
        value,
      );
      setDrawerMatch(updated);
      setRecord(updated);
      refresh();
    } catch (cause) {
      setDrawerError(errorMessage(cause));
    }
  }
  function back() {
    const previous = stack.at(-1);
    setStack((current) => current.slice(0, -1));
    if (previous?.kind === "match") {
      setDrawerMatch(previous.data);
      setRecord(previous.data);
    }
  }
  async function reconcileMatches() {
    setReconciling(true);
    setReconcileMessage("");
    setReconcileError("");
    try {
      const result = await threatIntelligenceService.reconcileMatches();
      setReconcileMessage(
        `Checked ${result.indicators_checked} active indicators; created ${result.matches_created} matches.`,
      );
      refresh();
    } catch (cause) {
      setReconcileError(errorMessage(cause));
    } finally {
      setReconciling(false);
    }
  }
  const recentPage = filters.page;
  const totalPages = data?.total_pages || 1;
  return (
    <main className="ti-page">
      <ThreatPageHeader
        title="Threat Matches"
        description="Investigate emails matching known threat indicators"
      >
        <button
          className="ti-button ti-button--secondary"
          disabled={loading}
          onClick={refresh}
        >
          <RefreshCw size={15} /> Refresh
        </button>
        {canInvestigate && (
          <button
            className="ti-button ti-button--secondary"
            disabled={loading || reconciling}
            onClick={reconcileMatches}
          >
            {reconciling ? "Matching existing emails…" : "Match existing emails"}
          </button>
        )}
      </ThreatPageHeader>
      {(reconcileMessage || reconcileError) && (
        <div className={reconcileError ? "ti-state ti-state--error" : "ti-state"} role="status">
          {reconcileError || reconcileMessage}
        </div>
      )}
      {error ? (
        <>
          <ThreatMatchFilters fields={fields} filters={filters} update={update} reset={reset} />
          <div className="ti-state ti-error">
            <strong>Threat matches could not be loaded.</strong>
            <span>{error}</span>
            <button className="ti-button ti-button--secondary" onClick={refresh}>
              Retry
            </button>
          </div>
        </>
      ) : !params ? (
        <>
          <ThreatMatchFilters fields={fields} filters={filters} update={update} reset={reset} />
          <div className="ti-state">
            Select both dates to load the custom period.
          </div>
        </>
      ) : (
        <>
          <ThreatSummaryCards
            loading={loading}
            items={
              summary
                ? [
                    {
                      label: "Total Matches",
                      value: summary.total_matches,
                      caption: "Current filters",
                    },
                    {
                      label: "Critical Matches",
                      value: summary.critical_matches,
                      caption: "Critical severity",
                    },
                    {
                      label: "Matched Emails",
                      value: summary.matched_emails,
                      caption: "Unique emails",
                    },
                    {
                      label: "Unique Indicators",
                      value: summary.unique_indicators,
                      caption: "Matched IOCs",
                    },
                  ]
                : [
                    "Total Matches",
                    "Critical Matches",
                    "Matched Emails",
                    "Unique Indicators",
                  ].map((label) => ({ label, value: 0 }))
            }
          />
          <ThreatMatchFilters fields={fields} filters={filters} update={update} reset={reset} />
          <section className="ti-panel">
            <header>
              <div>
                <h2>Threat Match Results</h2>
                <p>Matched email, indicator, feed and detection records</p>
              </div>
              <span className="ti-count">Total: {data?.total ?? "—"}</span>
            </header>
            {loading && !data ? (
              <div className="ti-empty">Loading threat matches…</div>
            ) : (
              <ThreatMatchTable items={data?.items || []} onView={view} />
            )}
            <footer className="email-pagination" aria-label="Threat matches pagination">
              <div className="email-pagination-summary">
                <span>{data?.total ? (recentPage - 1) * filters.page_size + 1 : 0} - {Math.min(recentPage * filters.page_size, data?.total || 0)}</span>
                <span>/ Total {data?.total || 0}</span>
              </div>
              <div className="email-pagination-controls">
                <button
                  type="button"
                  className="email-pagination-button"
                  aria-label="Go to previous page"
                  disabled={recentPage <= 1 || loading}
                  onClick={() => update("page", recentPage - 1)}
                >
                  <span aria-hidden="true">‹</span>
                  Previous
                </button>
                <span className="email-pagination-page">Page <strong>{recentPage}</strong> of <strong>{totalPages}</strong></span>
                <button
                  type="button"
                  className="email-pagination-button"
                  aria-label="Go to next page"
                  disabled={recentPage >= totalPages || loading}
                  onClick={() => update("page", recentPage + 1)}
                >
                  Next
                  <span aria-hidden="true">›</span>
                </button>
              </div>
            </footer>
          </section>
        </>
      )}
      <ThreatDrawer
        open={Boolean(drawerMatch)}
        title={
          record?.kind
            ? `${displayLabel(record.kind)} Details`
            : "Threat Match Details"
        }
        subtitle={
          record?.kind
            ? record.data?.id || record.id
            : drawerMatch?.indicator_value
        }
        onClose={() => {
          setDrawerMatch(null);
          setRecord(null);
          setStack([]);
        }}
        back={stack.length ? back : undefined}
      >
        <ThreatDrawerContent mode="details">
          {drawerLoading ? (
            <div className="ti-empty">Loading related record…</div>
          ) : record?.kind ? (
            <ThreatRelatedRecord kind={record.kind} data={record.data} />
          ) : (
            <ThreatMatchDetails
              match={drawerMatch}
              onRelated={related}
              onStatus={canInvestigate ? setStatus : undefined}
            />
          )}
          {drawerError && <div className="ti-form-error">{drawerError}</div>}
        </ThreatDrawerContent>
      </ThreatDrawer>
    </main>
  );
}

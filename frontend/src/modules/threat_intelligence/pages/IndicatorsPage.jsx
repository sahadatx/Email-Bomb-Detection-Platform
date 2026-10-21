import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import ThreatPageHeader from "../components/ThreatPageHeader";
import ThreatFilters from "../components/ThreatFilters";
import ThreatDrawer from "../components/ThreatDrawer";
import ThreatDrawerContent from "../components/ThreatDrawerContent";
import IndicatorTable from "../components/IndicatorTable";
import IndicatorForm from "../components/IndicatorForm";
import IndicatorDetails from "../components/IndicatorDetails";
import ThreatMatchDetails from "../components/ThreatMatchDetails";
import ThreatRelatedRecord from "../components/ThreatRelatedRecord";
import { apiRequest } from "../../../core/api/client";
import useThreatFilters from "../hooks/useThreatFilters";
import useIndicators from "../hooks/useIndicators";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage, displayDate } from "../types/threatIntelligence";
import "../styles/threatIntelligence.css";

const DEFAULTS = {
  search: "",
  indicator_type: "",
  severity: "",
  status: "",
  source: "",
  page: 1,
  page_size: 30,
};
export default function IndicatorsPage() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST"].includes(
    user?.role,
  );
  const { filters, query, update, reset } = useThreatFilters(DEFAULTS);
  const params = useMemo(() => {
    const { source, ...rest } = query;
    if (source?.startsWith("feed:"))
      return { ...rest, feed_id: source.slice("feed:".length) };
    return { ...rest, source: source || undefined };
  }, [query]);
  const { data, loading, error, refresh } = useIndicators(params);
  const [feeds, setFeeds] = useState([]);
  useEffect(() => {
    threatIntelligenceService
      .feeds({ page: 1, page_size: 100, sync_status: "success" })
      .then((result) => setFeeds(result.items || []))
      .catch(() => {});
  }, []);
  const [drawer, setDrawer] = useState({ mode: "closed", item: null });
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [related, setRelated] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [matchRelatedRecord, setMatchRelatedRecord] = useState(null);
  const [matchRelatedStack, setMatchRelatedStack] = useState([]);
  const [matchLoading, setMatchLoading] = useState(false);
  const [formDirty, setFormDirty] = useState(false);
  const pages = data?.total_pages || 1;
  const close = useCallback(() => {
    if (!busy) {
      setDrawer({ mode: "closed", item: null });
      setActionError("");
      setRelated([]);
      setSelectedMatch(null);
      setMatchRelatedRecord(null);
      setMatchRelatedStack([]);
    }
  }, [busy]);
  async function save(body) {
    setBusy(true);
    setActionError("");
    try {
      if (drawer.mode === "add")
        await threatIntelligenceService.createIndicator(body);
      else
        await threatIntelligenceService.updateIndicator(drawer.item.id, body);
      setNotice("Indicator saved.");
      setDrawer({ mode: "closed", item: null });
      refresh();
    } catch (cause) {
      setActionError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  async function toggle(item) {
    const next = item.status === "active" ? "inactive" : "active";
    if (
      !window.confirm(
        `${next === "inactive" ? "Disable" : "Enable"} ${item.value}?`,
      )
    )
      return;
    try {
      await threatIntelligenceService.setIndicatorStatus(item.id, next);
      setNotice(`Indicator ${next}.`);
      refresh();
    } catch (cause) {
      setNotice(errorMessage(cause));
    }
  }
  async function viewMatches() {
    setRelated([]);
    setSelectedMatch(null);
    setMatchRelatedRecord(null);
    setMatchRelatedStack([]);
    try {
      const result = await threatIntelligenceService.indicatorMatches(
        drawer.item.id,
        { page: 1, page_size: 10 },
      );
      setRelated(result.items);
      setDrawer((current) => ({ ...current, mode: "matches" }));
    } catch (cause) {
      setActionError(errorMessage(cause));
    }
  }
  async function viewMatchRelated(kind, id) {
    if (!id || !selectedMatch) return;
    setMatchRelatedStack((stack) => [...stack, matchRelatedRecord]);
    setMatchLoading(true);
    setActionError("");
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
      setMatchRelatedRecord({ kind, data: result });
      setDrawer((current) => ({ ...current, mode: "match-related" }));
    } catch (cause) {
      setActionError(errorMessage(cause));
    } finally {
      setMatchLoading(false);
    }
  }
  async function updateSelectedMatchStatus(matchStatus) {
    if (!selectedMatch) return;
    try {
      const updated = await threatIntelligenceService.updateMatchStatus(
        selectedMatch.id,
        matchStatus,
      );
      setSelectedMatch(updated);
      setActionError("");
    } catch (cause) {
      setActionError(errorMessage(cause));
    }
  }
  function backFromMatch() {
    if (drawer.mode === "match-related" && matchRelatedStack.length) {
      setMatchRelatedRecord(matchRelatedStack.at(-1) || null);
      setMatchRelatedStack((stack) => stack.slice(0, -1));
      setDrawer((current) => ({ ...current, mode: "match-detail" }));
      return;
    }
    if (drawer.mode === "match-detail") {
      setSelectedMatch(null);
      setDrawer((current) => ({ ...current, mode: "matches" }));
      return;
    }
    setDrawer((current) => ({ ...current, mode: "view" }));
  }
  const fields = [
    {
      key: "search",
      label: "Search",
      type: "search",
      placeholder: "Search indicators...",
    },
    {
      key: "indicator_type",
      label: "Indicator Type",
      kind: "type",
      allLabel: "All types",
    },
    {
      key: "severity",
      label: "Severity",
      kind: "severity",
      allLabel: "All severities",
    },
    {
      key: "status",
      label: "Status",
      kind: "status",
      options: ["active", "inactive", "expired"],
      allLabel: "All statuses",
    },
    {
      key: "source",
      label: "Source",
      options: [
        { value: "manual", label: "Manual" },
        ...feeds.map((feed) => ({ value: `feed:${feed.id}`, label: feed.name })),
      ],
      allLabel: "All sources",
    },
  ];
  return (
    <main className="ti-page">
      <ThreatPageHeader
        title="Indicators"
        description="Manage and investigate threat intelligence indicators"
      >
        <button
          className="ti-button ti-button--secondary"
          onClick={refresh}
          disabled={loading}
        >
          <RefreshCw size={15} /> Refresh
        </button>
        {canManage && (
          <button
            className="ti-button ti-button--primary"
            onClick={() => setDrawer({ mode: "add", item: null })}
          >
            <Plus size={16} /> Add Indicator
          </button>
        )}
      </ThreatPageHeader>
      <ThreatFilters
        className="ti-filters--indicators"
        fields={fields}
        values={filters}
        onChange={update}
        onReset={reset}
      />
      {notice && (
        <div className="ti-notice" role="status">
          {notice}
          <button onClick={() => setNotice("")}>Dismiss</button>
        </div>
      )}
      <section className="ti-panel">
        <header>
          <div>
            <h2>Indicator List</h2>
            <p>
              {(data?.total || 0).toLocaleString()} indicators · sourced from
              the threat intelligence database
            </p>
          </div>
          <span className="ti-count">Total: {data?.total ?? "—"}</span>
        </header>
        {error ? (
          <div className="ti-state ti-error">
            <strong>Indicators could not be loaded</strong>
            <span>{error}</span>
            <button
              className="ti-button ti-button--secondary"
              onClick={refresh}
            >
              Retry
            </button>
          </div>
        ) : loading && !data ? (
          <div className="ti-empty">Loading indicators…</div>
        ) : (
          <IndicatorTable
            items={data?.items || []}
            canManage={canManage}
            onView={(item) => setDrawer({ mode: "view", item })}
            onEdit={(item) => setDrawer({ mode: "edit", item })}
            onToggle={toggle}
          />
        )}
        <footer className="email-pagination" aria-label="Indicators pagination">
          <div className="email-pagination-summary">
            <span>{data?.total ? (filters.page - 1) * filters.page_size + 1 : 0} - {Math.min(filters.page * filters.page_size, data?.total || 0)}</span>
            <span>/ Total {data?.total || 0}</span>
          </div>
          <div className="email-pagination-controls">
            <button
              type="button"
              className="email-pagination-button"
              aria-label="Go to previous page"
              disabled={filters.page <= 1 || loading}
              onClick={() => update("page", filters.page - 1)}
            >
              <span aria-hidden="true">‹</span>
              Previous
            </button>
            <span className="email-pagination-page">Page <strong>{filters.page}</strong> of <strong>{pages}</strong></span>
            <button
              type="button"
              className="email-pagination-button"
              aria-label="Go to next page"
              disabled={filters.page >= pages || loading}
              onClick={() => update("page", filters.page + 1)}
            >
              Next
              <span aria-hidden="true">›</span>
            </button>
          </div>
        </footer>
      </section>
      <ThreatDrawer
        open={drawer.mode !== "closed"}
        title={
          drawer.mode === "add"
            ? "Add Indicator"
            : drawer.mode === "edit"
              ? "Edit Indicator"
              : drawer.mode === "matches"
                ? "Related Threat Matches"
                : drawer.mode === "match-detail"
                  ? "Threat Match Details"
                  : drawer.mode === "match-related"
                    ? `${matchRelatedRecord?.kind || "Related"} Details`
                    : "Indicator Details"
        }
        subtitle={
          drawer.mode.startsWith("match-")
            ? matchRelatedRecord?.data?.id || selectedMatch?.indicator_value
            : drawer.item?.value
        }
        onClose={close}
        busy={busy}
        dirty={formDirty}
        back={
          ["matches", "match-detail", "match-related"].includes(drawer.mode)
            ? backFromMatch
            : undefined
        }
        footer={
          drawer.mode === "add" || drawer.mode === "edit" ? (
            <>
              <button
                className="ti-button ti-button--secondary"
                onClick={close}
                disabled={busy}
              >
                Cancel
              </button>
              <button
                className="ti-button ti-button--primary"
                type="submit"
                form="ti-editor-form"
                disabled={busy}
              >
                {busy
                  ? "Saving…"
                  : drawer.mode === "add"
                    ? "Create Indicator"
                    : "Save Changes"}
              </button>
            </>
          ) : drawer.mode === "view" && canManage ? (
            <>
              <button
                className="ti-button ti-button--secondary"
                onClick={() => {
                  setFormDirty(false);
                  setDrawer((current) => ({ ...current, mode: "edit" }));
                }}
              >
                Edit
              </button>
              <button
                className="ti-button ti-button--secondary"
                onClick={() => toggle(drawer.item)}
              >
                {drawer.item.status === "active" ? "Disable" : "Enable"}
              </button>
            </>
          ) : null
        }
      >
        <ThreatDrawerContent mode={drawer.mode}>
          {drawer.mode === "add" || drawer.mode === "edit" ? (
            <IndicatorForm
              key={`${drawer.mode}-${drawer.item?.id || "new"}`}
              initial={drawer.mode === "edit" ? drawer.item : null}
              onSubmit={save}
              busy={busy}
              error={actionError}
              onDirtyChange={setFormDirty}
            />
          ) : drawer.mode === "matches" ? (
            related.length ? (
              related.map((match) => (
                <button
                  className="ti-match-mini ti-match-mini--button"
                  key={match.id}
                  onClick={() => {
                    setSelectedMatch(match);
                    setDrawer((current) => ({
                      ...current,
                      mode: "match-detail",
                    }));
                  }}
                >
                  <b>{match.email_label || match.email_id}</b>
                  <span>
                    {match.indicator_value} · {match.severity}
                  </span>
                  <span>
                    {displayDate(match.matched_at)} · {match.match_status}
                  </span>
                </button>
              ))
            ) : (
              <div className="ti-empty">No related matches found.</div>
            )
          ) : drawer.mode === "match-detail" ? (
            <ThreatMatchDetails
              match={selectedMatch}
              onRelated={viewMatchRelated}
              onStatus={canManage ? updateSelectedMatchStatus : undefined}
            />
          ) : drawer.mode === "match-related" ? (
            matchLoading ? (
              <div className="ti-empty">Loading related record…</div>
            ) : (
              <ThreatRelatedRecord
                kind={matchRelatedRecord?.kind}
                data={matchRelatedRecord?.data}
              />
            )
          ) : (
            <>
              <IndicatorDetails item={drawer.item} onMatches={viewMatches} />
            </>
          )}
          {actionError && !["add", "edit"].includes(drawer.mode) && (
            <p className="ti-form-error" role="alert">
              {actionError}
            </p>
          )}
        </ThreatDrawerContent>
      </ThreatDrawer>
    </main>
  );
}

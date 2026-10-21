import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import ThreatPageHeader from "../components/ThreatPageHeader";
import ThreatFilters from "../components/ThreatFilters";
import ThreatSummaryCards from "../components/ThreatSummaryCards";
import ThreatDrawer from "../components/ThreatDrawer";
import ThreatDrawerContent from "../components/ThreatDrawerContent";
import FeedList from "../components/FeedList";
import FeedForm from "../components/FeedForm";
import FeedSyncHistory from "../components/FeedSyncHistory";
import FeedSyncStatus from "../components/FeedSyncStatus";
import useThreatFilters from "../hooks/useThreatFilters";
import useThreatFeeds from "../hooks/useThreatFeeds";
import useFeedDetails from "../hooks/useFeedDetails";
import { threatIntelligenceService } from "../services/threatIntelligenceService";
import { errorMessage } from "../types/threatIntelligence";
import "../styles/threatIntelligence.css";

const DEFAULTS = {
  search: "",
  status: "",
  feed_type: "",
  sync_status: "",
  page: 1,
  page_size: 30,
};
export default function ThreatFeedsPage() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST"].includes(
    user?.role,
  );
  const { filters, query, update, reset } = useThreatFilters(DEFAULTS);
  const params = useMemo(() => query, [query]);
  const { data, loading, error, refresh } = useThreatFeeds(params);
  const [feedSummary, setFeedSummary] = useState(null);
  const [summaryError, setSummaryError] = useState("");
  const [summaryReload, setSummaryReload] = useState(0);
  const [drawer, setDrawer] = useState({ mode: "closed", item: null });
  const [busy, setBusy] = useState(false);
  const [errorText, setErrorText] = useState("");
  const [notice, setNotice] = useState("");
  const [syncingId, setSyncingId] = useState("");
  const [formDirty, setFormDirty] = useState(false);
  const selectedId = drawer.item?.id;
  const { data: detail, refresh: refreshDetail } = useFeedDetails(
    ["view", "sync"].includes(drawer.mode) ? selectedId : null,
  );
  useEffect(() => {
    if (
      data?.items?.some((feed) =>
        ["queued", "running"].includes(feed.sync_status),
      )
    ) {
      const timer = window.setInterval(refresh, 2500);
      return () => window.clearInterval(timer);
    }
    return undefined;
  }, [data, refresh]);
  useEffect(() => {
    if (
      drawer.mode !== "sync" ||
      !selectedId ||
      !["queued", "running"].includes(
        detail?.sync_status || drawer.item?.sync_status,
      )
    )
      return undefined;
    const timer = window.setInterval(() => {
      refreshDetail();
      refresh();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [
    drawer.mode,
    selectedId,
    detail?.sync_status,
    drawer.item?.sync_status,
    refreshDetail,
    refresh,
  ]);
  useEffect(() => {
    let current = true;
    setSummaryError("");
    threatIntelligenceService
      .feedSummary()
      .then((summary) => {
        if (current) setFeedSummary(summary);
      })
      .catch((cause) => {
        if (current) {
          setFeedSummary(null);
          setSummaryError(errorMessage(cause));
        }
      });
    return () => {
      current = false;
    };
  }, [data?.items, drawer.mode, summaryReload]);
  const close = useCallback(() => {
    if (!busy) {
      setDrawer({ mode: "closed", item: null });
      setErrorText("");
      setSyncingId("");
    }
  }, [busy]);
  async function save(body) {
    setBusy(true);
    setErrorText("");
    try {
      if (drawer.mode === "add")
        await threatIntelligenceService.createFeed(body);
      else await threatIntelligenceService.updateFeed(drawer.item.id, body);
      setNotice("Feed configuration saved.");
      setDrawer({ mode: "closed", item: null });
      refresh();
    } catch (cause) {
      setErrorText(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }
  async function sync() {
    setBusy(true);
    setErrorText("");
    setSyncingId(drawer.item.id);
    try {
      await threatIntelligenceService.syncFeed(drawer.item.id);
      setDrawer((current) => ({ ...current, mode: "sync" }));
      refresh();
      refreshDetail();
    } catch (cause) {
      setErrorText(errorMessage(cause));
      setSyncingId("");
    } finally {
      setBusy(false);
    }
  }
  const fields = [
    {
      key: "search",
      label: "Search",
      type: "search",
      placeholder: "Search feeds...",
    },
    {
      key: "status",
      label: "Status",
      allLabel: "All statuses",
      options: ["active", "inactive"],
    },
    {
      key: "feed_type",
      label: "Feed Type",
      kind: "feed_type",
      allLabel: "All types",
    },
    {
      key: "sync_status",
      label: "Sync Status",
      allLabel: "All sync statuses",
      options: ["never_synced", "queued", "running", "success", "failed"],
    },
  ];
  const summaryItems = [
    {
      label: "Total Feeds",
      value: feedSummary?.total_feeds || 0,
      caption: "Configured sources",
    },
    {
      label: "Active Feeds",
      value: feedSummary?.active_feeds || 0,
      caption: "Enabled sources",
    },
    {
      label: "Sync Failed",
      value: feedSummary?.sync_failed || 0,
      caption: "Require attention",
    },
    {
      label: "Imported Indicators",
      value: feedSummary?.imported_indicators || 0,
      caption: "From all feeds",
    },
  ];
  const currentDetail = detail || drawer.item;
  return (
    <main className="ti-page">
      <ThreatPageHeader
        title="Threat Feeds"
        description="Manage threat intelligence sources and synchronization"
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
            <Plus size={16} /> Add Feed
          </button>
        )}
      </ThreatPageHeader>
      {notice && (
        <div className="ti-notice">
          {notice}
          <button onClick={() => setNotice("")}>Dismiss</button>
        </div>
      )}
      {summaryError ? (
        <div className="ti-state ti-error" role="alert">
          <strong>Feed summary could not be loaded.</strong>
          <span>{summaryError}</span>
          <button
            className="ti-button ti-button--secondary"
            onClick={() => setSummaryReload((value) => value + 1)}
          >
            Retry
          </button>
        </div>
      ) : (
        <ThreatSummaryCards
          items={summaryItems}
          loading={loading || !feedSummary}
        />
      )}
      <ThreatFilters
        fields={fields}
        values={filters}
        onChange={update}
        onReset={reset}
        className="ti-filters--feeds"
      />
      <section className="ti-panel">
        <header>
          <div>
            <h2>Threat Feed List</h2>
            <p>{data?.total?.toLocaleString?.() ?? "—"} configured sources</p>
          </div>
          <span className="ti-count">Total: {data?.total ?? "—"}</span>
        </header>
        {error ? (
          <div className="ti-state ti-error">
            <strong>Feeds could not be loaded</strong>
            <span>{error}</span>
            <button
              className="ti-button ti-button--secondary"
              onClick={refresh}
            >
              Retry
            </button>
          </div>
        ) : loading && !data ? (
          <div className="ti-empty">Loading threat feeds…</div>
        ) : (
          <FeedList
            items={data?.items || []}
            canManage={canManage}
            syncingId={syncingId}
            onView={(item) => setDrawer({ mode: "view", item })}
            onEdit={(item) => setDrawer({ mode: "edit", item })}
            onSync={(item) => setDrawer({ mode: "sync", item })}
          />
        )}
        <footer className="email-pagination" aria-label="Threat feeds pagination">
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
            <span className="email-pagination-page">Page <strong>{filters.page}</strong> of <strong>{data?.total_pages || 1}</strong></span>
            <button
              type="button"
              className="email-pagination-button"
              aria-label="Go to next page"
              disabled={filters.page >= (data?.total_pages || 1) || loading}
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
            ? "Add Threat Feed"
            : drawer.mode === "edit"
              ? "Edit Threat Feed"
              : drawer.mode === "sync"
                ? "Synchronize Feed"
                : "Threat Feed Details"
        }
        subtitle={drawer.item?.name}
        onClose={close}
        dirty={formDirty}
        busy={busy}
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
                    ? "Create Feed"
                    : "Save Changes"}
              </button>
            </>
          ) : drawer.mode === "sync" &&
            currentDetail?.sync_status !== "running" &&
            currentDetail?.sync_status !== "queued" ? (
            <>
              <button
                className="ti-button ti-button--secondary"
                onClick={close}
              >
                Close
              </button>
              <button
                className="ti-button ti-button--primary"
                onClick={() =>
                  setDrawer((current) => ({ ...current, mode: "view" }))
                }
              >
                Feed Details
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
              {drawer.item?.feed_type !== "internal" && (
                <button
                  className="ti-button ti-button--primary"
                  disabled={
                    !drawer.item?.enabled ||
                    ["running", "queued"].includes(currentDetail?.sync_status)
                  }
                  onClick={() =>
                    setDrawer((current) => ({ ...current, mode: "sync" }))
                  }
                >
                  Sync Now
                </button>
              )}
            </>
          ) : null
        }
      >
        <ThreatDrawerContent mode={drawer.mode}>
          {["add", "edit"].includes(drawer.mode) ? (
            <FeedForm
              key={`${drawer.mode}-${drawer.item?.id || "new"}`}
              initial={drawer.mode === "edit" ? drawer.item : null}
              onSubmit={save}
              busy={busy}
              error={errorText}
              onDirtyChange={setFormDirty}
            />
          ) : drawer.mode === "sync" ? (
            <div className="ti-sync-confirm">
              <h3>
                {["queued", "running"].includes(currentDetail?.sync_status)
                  ? "Synchronization in progress"
                  : "Ready to synchronize this feed?"}
              </h3>
              <p>
                Remote content will be fetched over HTTPS, validated and
                imported as indicators. Feed credentials stay encrypted and are
                never returned by the API.
              </p>
              {errorText && <div className="ti-form-error">{errorText}</div>}
              {["queued", "running"].includes(currentDetail?.sync_status) ? (
                <FeedSyncStatus feed={currentDetail} />
              ) : (
                <button
                  className="ti-button ti-button--primary"
                  disabled={busy}
                  onClick={sync}
                >
                  {busy ? "Queueing…" : "Confirm Sync"}
                </button>
              )}
              <h3>Sync History</h3>
              <FeedSyncHistory
                items={currentDetail?.sync_history?.items || []}
              />
            </div>
          ) : currentDetail ? (
            <>
              <FeedSyncStatus feed={currentDetail} />
              <dl className="ti-definition-list">
                <dt>Name</dt>
                <dd>{currentDetail.name}</dd>
                <dt>Type</dt>
                <dd>{currentDetail.feed_type}</dd>
                <dt>URL</dt>
                <dd>{currentDetail.url || "Internal source"}</dd>
                <dt>Authentication</dt>
                <dd>
                  {currentDetail.auth_type}
                  {currentDetail.has_credential ? " · secret saved" : ""}
                </dd>
                <dt>Sync interval</dt>
                <dd>{currentDetail.sync_interval_minutes} minutes</dd>
                <dt>Description</dt>
                <dd>{currentDetail.description || "—"}</dd>
              </dl>
              <h3>Synchronization History</h3>
              <FeedSyncHistory
                items={currentDetail.sync_history?.items || []}
              />
            </>
          ) : (
            <div className="ti-empty">Loading feed details…</div>
          )}
        </ThreatDrawerContent>
      </ThreatDrawer>
    </main>
  );
}

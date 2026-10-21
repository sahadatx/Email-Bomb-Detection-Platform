import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, Search, X } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import AdminPageHeader from "../components/common/AdminPageHeader";
import SummaryCards from "../components/common/SummaryCards";
import Pagination from "../components/common/Pagination";
import { EmptyState, ErrorState } from "../components/common/EmptyErrorState";
import AuditTable from "../components/audit/AuditTable";
import AuditDetailsDrawer from "../components/audit/AuditDetailsDrawer";
import { auditService } from "../services/auditService";
import { errorMessage } from "../types";

const DEFAULT = { action: "", actor_id: "", status: "", severity: "", source: "", from_date: "", to_date: "" };

export default function AuditLogsPage() {
  const { user } = useAuth();
  const canExport = ["ADMIN", "SECURITY_ANALYST"].includes(user?.role);
  const [rows, setRows] = useState([]); const [summary, setSummary] = useState(null); const [options, setOptions] = useState({ actions: [], actors: [], sources: [] });
  const [filters, setFilters] = useState(DEFAULT);
  const [search, setSearch] = useState(""); const [page, setPage] = useState(1); const [sortBy, setSortBy] = useState("created_at"); const [sortOrder, setSortOrder] = useState("desc");
  const [total, setTotal] = useState(0); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [selected, setSelected] = useState(null); const [detailLoading, setDetailLoading] = useState(false); const [exporting, setExporting] = useState(false); const [toast, setToast] = useState("");

  const params = useMemo(() => ({ ...filters, page, page_size: 30, search: search.trim(), sort_by: sortBy, sort_order: sortOrder }), [filters, page, search, sortBy, sortOrder]);
  const refresh = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [list, stats] = await Promise.all([auditService.list(params), auditService.summary({ from_date: filters.from_date, to_date: filters.to_date })]);
      setRows(list.items || []); setTotal(list.total || 0); setSummary(stats);
    } catch (cause) { setError(errorMessage(cause)); setRows([]); setTotal(0); setSummary(null); }
    finally { setLoading(false); }
  }, [params, filters.from_date, filters.to_date]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { auditService.options().then(setOptions).catch(() => {}); }, []);

  async function showDetails(row) { setDetailLoading(true); setSelected({ ...row, loading: true }); try { setSelected(await auditService.detail(row.id)); } catch (cause) { setSelected({ ...row, detailError: errorMessage(cause) }); } finally { setDetailLoading(false); } }
  async function exportRows() { setExporting(true); try { await auditService.export({ ...filters, search: search.trim(), format: "csv", limit: 10000 }); setToast("Audit log export downloaded."); } catch (cause) { setError(errorMessage(cause)); } finally { setExporting(false); } }
  function updateFilter(key, value) { setFilters((current) => ({ ...current, [key]: value })); setPage(1); }
  function sort(key) { if (sortBy === key) setSortOrder((value) => value === "asc" ? "desc" : "asc"); else { setSortBy(key); setSortOrder("desc"); } setPage(1); }
  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return <main className="asa-page"><AdminPageHeader title="Audit Logs" description="Monitor, search and review traceable system activity." onRefresh={refresh} loading={loading}/>
    {toast && <div className="asa-toast" role="status">{toast}<button onClick={() => setToast("")}><X size={14}/></button></div>}
    <SummaryCards loading={!summary && loading} items={summary ? [{ label: "Total Events", value: summary.total_events, description: "In selected time range" }, { label: "Failed Actions", value: summary.failed_actions, description: "Operations recorded as failed" }, { label: "Security Events", value: summary.security_events, description: "Events with severity" }, { label: "Active Users", value: summary.active_users, description: "Unique actors in range" }] : [{ label: "Total Events", value: "—" }, { label: "Failed Actions", value: "—" }, { label: "Security Events", value: "—" }, { label: "Active Users", value: "—" }]}/>
    <section className="asa-panel"><div className="asa-panel-heading"><div><h2>Recent Events</h2><p>Authentication, user management, detection and administrative activity.</p></div></div>
      <div className="asa-filter-row"><label className="asa-search"><Search size={16}/><input placeholder="Search actor, action, target, IP address, event ID…" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }}/></label><label>Action<select value={filters.action} onChange={(e) => updateFilter("action", e.target.value)}><option value="">All actions</option>{options.actions.map((value) => <option key={value}>{value}</option>)}</select></label><label>Actor<select value={filters.actor_id} onChange={(e) => updateFilter("actor_id", e.target.value)}><option value="">All actors</option>{options.actors.map((actor, index) => <option key={`${actor.id}-${index}`} value={actor.id}>{actor.name}</option>)}</select></label><label>Status<select value={filters.status} onChange={(e) => updateFilter("status", e.target.value)}><option value="">All statuses</option><option value="success">Success</option><option value="failure">Failure</option></select></label><label>Severity<select value={filters.severity} onChange={(e) => updateFilter("severity", e.target.value)}><option value="">All severities</option>{["critical", "high", "medium", "low"].map((value) => <option key={value}>{value}</option>)}</select></label><label>Source<select value={filters.source} onChange={(e) => updateFilter("source", e.target.value)}><option value="">All sources</option>{options.sources.map((value) => <option key={value}>{value}</option>)}</select></label><label>From<input type="date" value={filters.from_date} onChange={(e) => updateFilter("from_date", e.target.value)}/></label><label>To<input type="date" value={filters.to_date} onChange={(e) => updateFilter("to_date", e.target.value)}/></label></div>
      <div className="asa-filter-actions"><span>{activeFilterCount ? `${activeFilterCount} active filters` : "Filter audit events"}</span><div><button className="asa-button asa-button--secondary" onClick={() => { setFilters(DEFAULT); setSearch(""); setPage(1); }}>Reset Filters</button><button className="asa-button asa-button--primary" disabled={!canExport || exporting} title={!canExport ? "Export permission required" : undefined} onClick={exportRows}><Download size={15}/>{exporting ? "Exporting…" : "Export Logs"}</button></div></div>
      {error ? <ErrorState error={error} onRetry={refresh}/> : loading ? <div className="asa-state">Loading audit events…</div> : rows.length ? <><AuditTable items={rows} sortBy={sortBy} sortOrder={sortOrder} onSort={sort} onView={showDetails}/><Pagination className="asa-pagination--email" page={page} pageSize={30} total={total} onPage={setPage}/></> : <EmptyState title={search || activeFilterCount ? "No events match these filters" : "No audit events yet"} description="Audit events appear as audited platform actions are performed."/>}
    </section>
    <AuditDetailsDrawer event={selected} onClose={() => setSelected(null)} loading={detailLoading}/>
  </main>;
}

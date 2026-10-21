import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpRight, FlaskConical } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import ExperimentFilters from "../components/ExperimentFilters";
import ExperimentSummaryCards from "../components/ExperimentSummaryCards";
import ExperimentTable from "../components/ExperimentTable";
import ExperimentComparison from "../components/ExperimentComparison";
import ExperimentPageHeader from "../components/ExperimentPageHeader";
import ExperimentPagination from "../components/ExperimentPagination";
import ExperimentActionSidebar from "../components/ExperimentActionSidebar";
import ExperimentCreateDrawer from "../components/ExperimentCreateDrawer";
import useExperimentComparison from "../hooks/useExperimentComparison";
import { experimentsService } from "../services/experimentsService";
import { errorText } from "../types";
import "../styles/experiments.css";

const PAGE_SIZE = 30;
const DEFAULT_FILTERS = { search: "", status: "", model_definition_id: "", dataset_version_id: "", from_date: "", to_date: "", sort: "newest" };

export default function ExperimentsPage() {
  const navigate = useNavigate(); const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST", "EMAIL_ANALYST"].includes(user?.role);
  const [filters, setFilters] = useState(DEFAULT_FILTERS); const [debouncedSearch, setDebouncedSearch] = useState("");
  const [models, setModels] = useState([]); const [sources, setSources] = useState([]);
  const [items, setItems] = useState([]); const [summary, setSummary] = useState(null); const [page, setPage] = useState(1); const [total, setTotal] = useState(0); const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [busyId, setBusyId] = useState(""); const [toast, setToast] = useState(""); const [selected, setSelected] = useState([]); const [viewItem, setViewItem] = useState(null); const [createOpen, setCreateOpen] = useState(false); const { items: comparison, loading: compareLoading, error: compareError, compare: compareRuns, clear: clearComparison } = useExperimentComparison();
  useEffect(() => { const timer = window.setTimeout(() => setDebouncedSearch(filters.search), 250); return () => window.clearTimeout(timer); }, [filters.search]);
  useEffect(() => { experimentsService.options().then((value) => { setModels(value.models || []); setSources(value.preprocessing_runs || []); }).catch((cause) => setError(errorText(cause))); }, []);
  const params = useMemo(() => {
    const from_date = filters.from_date ? `${filters.from_date}T00:00:00Z` : undefined;
    const to_date = filters.to_date ? `${filters.to_date}T23:59:59Z` : undefined;
    return { page, page_size: PAGE_SIZE, search: debouncedSearch.trim(), status: filters.status, model_definition_id: filters.model_definition_id, dataset_version_id: filters.dataset_version_id, from_date, to_date, sort: filters.sort };
  }, [page, debouncedSearch, filters]);
  const load = useCallback(async (quiet = false) => {
    if (filters.from_date && filters.to_date && filters.from_date > filters.to_date) { setItems([]); setTotal(0); setLoading(false); return; }
    if (!quiet) { setLoading(true); setError(""); }
    try { const result = await experimentsService.list(params); setItems(result.items || []); setTotal(result.total || 0); setTotalPages(result.total_pages || 1); setSummary(result.summary || null); }
    catch (cause) { if (!quiet) { setError(errorText(cause)); setItems([]); setTotal(0); } }
    finally { if (!quiet) setLoading(false); }
  }, [params, filters.from_date, filters.to_date]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (!items.some((item) => ["queued", "running"].includes(item.status))) return undefined; const timer = window.setInterval(() => load(true), 3000); return () => window.clearInterval(timer); }, [items, load]);
  function update(key, value) { setFilters((current) => ({ ...current, [key]: value })); setPage(1); }
  function reset() { setFilters(DEFAULT_FILTERS); setPage(1); setSelected([]); }
  function toggle(id) { setSelected((current) => current.includes(id) ? current.filter((value) => value !== id) : current.length < 5 ? [...current, id] : current); }
  async function start(item) { if (!canManage) return; setBusyId(item.id); try { const run = await experimentsService.startRun(item.id); navigate(`/experiments/${item.id}/runs/${run.id}`); } catch (cause) { setError(errorText(cause)); } finally { setBusyId(""); } }
  async function remove(item) { if (!canManage || !window.confirm(`Delete experiment “${item.name}”? Its linked ML training and evaluation records will remain in ML Model Management.`)) return; setBusyId(item.id); try { await experimentsService.remove(item.id); setToast("Experiment deleted."); setSelected((current) => current.filter((id) => id !== item.id)); await load(); } catch (cause) { setError(errorText(cause)); } finally { setBusyId(""); } }
  async function compare() { if (selected.length < 2) return; await compareRuns(selected); }
  return <main className="ex-page"><ExperimentPageHeader onRefresh={() => load()} onCreate={() => setCreateOpen(true)} loading={loading} canManage={canManage}/>
    {toast && <div className="ex-toast" role="status">{toast}<button onClick={() => setToast("")}>Dismiss</button></div>}
    <ExperimentSummaryCards summary={summary} loading={loading && !summary}/>
    <section className="ex-panel"><div className="ex-panel-heading"><div><h2>Experiment Runs</h2><p>{total.toLocaleString()} total · experiment values come from linked ML training and evaluation records</p></div><span className="ex-count">{total.toLocaleString()} total</span></div>
      <ExperimentFilters filters={filters} models={models} datasets={sources} update={update} reset={reset} loading={loading}/>
      {error ? <div className="ex-state ex-state--error"><strong>Experiments could not be loaded</strong><span>{error}</span><button className="ex-button ex-button--secondary" onClick={() => load()}>Retry</button></div> : loading && !items.length ? <div className="ex-empty">Loading experiment records…</div> : items.length ? <><ExperimentTable items={items} selected={selected} onSelect={toggle} onView={setViewItem} onRun={start} onDelete={remove} canManage={canManage} busyId={busyId}/><ExperimentPagination page={page} pageSize={PAGE_SIZE} total={total} totalPages={totalPages} loading={loading} onPageChange={setPage}/></> : <div className="ex-state"><FlaskConical size={25}/><strong>{Object.values(filters).some(Boolean) ? "No experiments match these filters" : "No experiments yet"}</strong><span>Create an experiment to reuse existing datasets and ML model workflows.</span>{canManage && <button type="button" className="ex-button ex-button--primary" onClick={() => setCreateOpen(true)}>New Experiment <ArrowUpRight size={15}/></button>}</div>}
    </section>
    {selected.length > 0 && <div className="ex-selection-bar"><span>{selected.length} completed experiment{selected.length === 1 ? "" : "s"} selected (up to 5)</span><button className="ex-button ex-button--primary" disabled={selected.length < 2 || compareLoading} onClick={compare}>Compare selected</button></div>}
    {(comparison.length > 0 || compareLoading || compareError) && <ExperimentComparison items={comparison} loading={compareLoading} error={compareError} onClose={clearComparison}/ >}
    <ExperimentActionSidebar item={viewItem} onClose={() => setViewItem(null)}/>
    <ExperimentCreateDrawer open={createOpen} onClose={() => setCreateOpen(false)}/>
  </main>;
}

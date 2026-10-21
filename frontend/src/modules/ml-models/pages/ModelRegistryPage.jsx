import { useCallback, useEffect, useMemo, useState } from "react";
import { Eye } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../../core/auth/AuthProvider";
import { getVersions, getVersionById, activateVersion, archiveVersion, restoreVersion, downloadVersionArtifact } from "../services/modelRegistryService";
import { modelService } from "../services/modelService";
import { getTrainingRunById, getPreprocessingRun } from "../services/trainingRunService";
import { getEvaluationRuns } from "../services/evaluationService";
import ModelPagination from "../components/ModelPagination";
import "../styles/ml-models.css";

const text = (e) => e?.response?.data?.detail?.message || e?.response?.data?.detail || e?.message || "Request failed.";
const date = (v) => v ? new Date(v).toLocaleString() : "—";
const size = (v) => v == null ? "—" : `${(v / 1024 / 1024).toFixed(2)} MB`;
const PAGE_SIZE = 30;

export default function ModelRegistryPage() {
  const { user } = useAuth();
  const canManage = ["ADMIN", "SECURITY_ANALYST"].includes(user?.role);
  const [searchParams] = useSearchParams();
  const [versions, setVersions] = useState([]); const [models, setModels] = useState([]); const [evaluations, setEvaluations] = useState([]); const [total, setTotal] = useState(0); const [allTotal, setAllTotal] = useState(0); const [modelTotal, setModelTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState(""); const [status, setStatus] = useState(""); const [modelId, setModelId] = useState("");
  const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [toast, setToast] = useState(""); const [busyId, setBusyId] = useState("");
  const [detail, setDetail] = useState(null); const [model, setModel] = useState(null); const [training, setTraining] = useState(null); const [preprocessing, setPreprocessing] = useState(null); const [detailEvaluations, setDetailEvaluations] = useState([]); const [detailError, setDetailError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [versionsResponse, modelResponse, evaluationResponse, summaryResponse] = await Promise.all([
        getVersions({ offset: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE, search: search.trim() || undefined, status: status || undefined, model_definition_id: modelId || undefined }),
        modelService.getModels({ offset: 0, limit: 200 }),
        getEvaluationRuns({ offset: 0, limit: 200 }), modelService.getSummary(),
      ]);
      setVersions(versionsResponse.items || []); setTotal(versionsResponse.total || 0); setModels(Array.isArray(modelResponse) ? modelResponse : modelResponse.items || []); setEvaluations(evaluationResponse.items || []); setModelTotal(summaryResponse.total_models || 0);
    } catch (e) { setError(text(e)); }
    finally { setLoading(false); }
  }, [search, status, modelId, page]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { const id = searchParams.get("version_id"); if (id) openDetails({ id }); }, []);

  const modelMap = useMemo(() => Object.fromEntries(models.map((m) => [m.id, m])), [models]);
  async function openDetails(row) {
    setDetail(row); setModel(null); setTraining(null); setPreprocessing(null); setDetailEvaluations([]); setDetailError("");
    try {
      const version = await getVersionById(row.id); setDetail(version);
      const [modelResult, runResult, evalResult] = await Promise.allSettled([
        modelService.getModelById(version.model_definition_id),
        getTrainingRunById(version.training_run_id),
        getEvaluationRuns({ model_version_id: version.id, offset: 0, limit: 20 }),
      ]);
      if (modelResult.status === "fulfilled") setModel(modelResult.value);
      if (runResult.status === "fulfilled") setTraining(runResult.value);
      if (evalResult.status === "fulfilled") setDetailEvaluations(evalResult.value.items || []);
      if (runResult.status === "fulfilled") {
        try { setPreprocessing(await getPreprocessingRun(runResult.value.preprocessing_run_id)); } catch { /* The version details still remain available without dataset display metadata. */ }
      }
    } catch (e) { setDetailError(text(e)); }
  }
  async function action(kind, row) {
    const modelName = modelMap[row.model_definition_id]?.name || row.model_definition_id;
    if (!window.confirm(`${kind} ${modelName} version ${row.version}?`)) return;
    setBusyId(row.id); setError(""); setDetailError("");
    try {
      if (kind === "Activate") await activateVersion(row.id);
      if (kind === "Archive") await archiveVersion(row.id);
      if (kind === "Restore") await restoreVersion(row.id);
      await load();
      if (detail?.id === row.id) await openDetails(row);
      setToast(`Version ${row.version} ${kind.toLowerCase()}d.`);
    } catch (e) { const msg = text(e); if (detail?.id === row.id) setDetailError(msg); else setError(msg); }
    finally { setBusyId(""); }
  }
  async function downloadArtifact(version) {
    setBusyId(version.id); setDetailError("");
    try { await downloadVersionArtifact(version.id); setToast("Artifact download started; backend checksum validation passed."); }
    catch (e) { setDetailError(text(e)); }
    finally { setBusyId(""); }
  }

  const counts = async (filter) => { try { return (await getVersions({ ...filter, offset: 0, limit: 1 })).total || 0; } catch { return 0; } };
  const hasFilters = Boolean(search || status || modelId);
  const resetFilters = () => { setPage(1); setSearch(""); setStatus(""); setModelId(""); };
  const [summary, setSummary] = useState({ active: 0, registered: 0, archived: 0 });
  useEffect(() => { Promise.all([counts({}), counts({ status: "active" }), counts({ status: "registered" }), counts({ status: "archived" })]).then(([all, active, registered, archived]) => { setAllTotal(all); setSummary({ active, registered, archived }); }); }, [total]);

  return <main className="ml-page ml-registry-page">
    <header className="ml-page-header"><div><h1>Model Registry</h1><p>Manage registered model versions and artifacts.</p></div><button className="ml-button ml-button--secondary" onClick={load} disabled={loading}>Refresh</button></header>
    <section className="ml-summary-grid">{[["Registered Versions", allTotal], ["Active Versions", summary.active], ["Archived Versions", summary.archived], ["Models", modelTotal]].map(([label, value]) => <article className="ml-summary-card" key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
    {error && <div className="ml-inline-error" role="alert">{error} <button className="ml-button ml-button--small" onClick={load}>Retry</button></div>}
    <section className="ml-panel"><div className="ml-panel__header"><div><h2>Registered Versions</h2><p>Versions are created from successful training runs with artifacts.</p></div><span className="ml-panel__count">{total} versions</span></div>
      <div className="ml-toolbar"><input value={search} onChange={(e) => { setPage(1); setSearch(e.target.value); }} placeholder="Search model, version, or training run..." aria-label="Search registry"/><select value={status} onChange={(e) => { setPage(1); setStatus(e.target.value); }} aria-label="Filter registry status"><option value="">All statuses</option>{["registered", "active", "archived"].map((s) => <option key={s}>{s}</option>)}</select><select value={modelId} onChange={(e) => { setPage(1); setModelId(e.target.value); }} aria-label="Filter model"><option value="">All models</option>{models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select></div><div className="ml-filter-actions"><span>{hasFilters ? "Filters applied to registered versions." : "Filter registered versions."}</span><button className="ml-button ml-button--secondary" type="button" disabled={!hasFilters} onClick={resetFilters}>Reset Filters</button></div>
      {loading && !versions.length ? <div className="ml-empty-state">Loading model versions…</div> : !loading && !error && !versions.length ? <div className="ml-empty-state">{search || status || modelId ? "No versions match these filters." : "No registered versions yet. Complete a training run to create one."}</div> : <div className="ml-table-scroll"><table className="ml-data-table"><thead><tr><th>Model</th><th>Version</th><th>Source Training Run</th><th>Accuracy Result</th><th>Registered At</th><th>Status</th><th>Actions</th></tr></thead><tbody>{versions.map((v) => { const related = evaluations.find((ev) => ev.model_version_id === v.id && ev.status === "completed"); return <tr key={v.id}><td title={modelMap[v.model_definition_id]?.name || v.model_definition_id}>{modelMap[v.model_definition_id]?.name || v.model_definition_id}</td><td>v{v.version}</td><td>{canManage ? <button className="ml-text-button" title={v.training_run_id} onClick={() => window.location.assign(`/ml-models/training-runs?run_id=${encodeURIComponent(v.training_run_id)}`)}>{v.training_run_id}</button> : v.training_run_id}</td><td>{related?.accuracy == null ? "—" : `${(related.accuracy * 100).toFixed(2)}%`}</td><td>{date(v.created_at)}</td><td><span className={`ml-version-status ml-version-status--${v.status}`}>{v.status}</span></td><td className="ml-row-actions"><button className="ml-registry-view-link" onClick={() => openDetails(v)}><Eye size={14} aria-hidden="true"/>View</button>{canManage && v.status === "registered" && <button className="ml-button ml-button--small ml-button--primary" disabled={busyId === v.id} onClick={() => action("Activate", v)}>Activate</button>}{canManage && v.status === "archived" && <button className="ml-button ml-button--small ml-button--secondary" disabled={busyId === v.id} onClick={() => action("Restore", v)}>Restore</button>}{canManage && v.status !== "archived" && <button className="ml-button ml-button--small ml-button--danger" disabled={busyId === v.id} onClick={() => action("Archive", v)}>Archive</button>}</td></tr>; })}</tbody></table></div>}
      <ModelPagination page={page} pageSize={PAGE_SIZE} total={total} loading={loading} onPage={setPage} />
    </section>
    {detail && <div className="ml-drawer-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setDetail(null); }}><aside className="ml-drawer ml-drawer--details" role="dialog" aria-modal="true"><header className="ml-drawer__header"><div><span className="ml-eyebrow">MODEL REGISTRY</span><h2>{model?.name || "Model version"} · v{detail.version}</h2><p>Artifact, source run and evaluation information.</p></div><button className="ml-icon-button" aria-label="Close drawer" onClick={() => setDetail(null)}>×</button></header><div className="ml-drawer__body">{detailError && <div className="ml-alert ml-alert--error">{detailError}</div>}<dl className="ml-details-list">{[["Model ID", detail.model_definition_id], ["Status", detail.status], ["Training Run", training?.id || detail.training_run_id], ["Preprocessing Run", training?.preprocessing_run_id], ["Dataset Version", preprocessing?.dataset_version_name || preprocessing?.dataset_version_id], ["Artifact", detail.artifact_filename], ["Format", detail.media_type], ["Size", size(detail.size_bytes)], ["Checksum", detail.checksum_sha256], ["Integrity", detail.checksum_sha256 ? "Backend verifies checksum on download/activation" : "No checksum recorded"], ["Created", date(detail.created_at)], ["Activated", date(detail.activated_at)], ["Archived", date(detail.archived_at)]].map(([k,v]) => <div key={k}><dt>{k}</dt><dd>{v || "—"}</dd></div>)}</dl><h3>Accuracy</h3>{detailEvaluations.length ? <ul className="ml-related-list">{detailEvaluations.map((e) => <li key={e.id}><button className="ml-text-button" onClick={() => window.location.assign(`/ml-models/evaluation?evaluation_id=${encodeURIComponent(e.id)}`)}>{e.id}</button> · {e.evaluation_split} · {e.status} · Accuracy {e.accuracy == null ? "—" : `${(e.accuracy * 100).toFixed(2)}%`}</li>)}</ul> : <p>No accuracy result is available for this version.</p>}<h3>Artifact metadata</h3><pre className="ml-json-view">{JSON.stringify(detail.metadata_json || {}, null, 2)}</pre></div><footer className="ml-drawer__footer ml-drawer__footer--static">{canManage && <button className="ml-button ml-button--secondary" onClick={() => window.location.assign(`/ml-models/training-runs?run_id=${encodeURIComponent(detail.training_run_id)}`)}>View Training Run</button>}{canManage && <button className="ml-button ml-button--secondary" disabled={busyId === detail.id} onClick={() => downloadArtifact(detail)}>{busyId === detail.id ? "Downloading…" : "Download Artifact"}</button>}{canManage && detail.status === "registered" && <button className="ml-button ml-button--primary" disabled={busyId === detail.id} onClick={() => action("Activate", detail)}>Activate</button>}{canManage && detail.status === "archived" && <button className="ml-button ml-button--primary" disabled={busyId === detail.id} onClick={() => action("Restore", detail)}>Restore</button>}{canManage && detail.status !== "archived" && <button className="ml-button ml-button--danger" disabled={busyId === detail.id} onClick={() => action("Archive", detail)}>Archive</button>}</footer></aside></div>}
    {toast && <div className="ml-toast" role="status" onAnimationEnd={() => setToast("")}>{toast}</div>}
  </main>;
}
